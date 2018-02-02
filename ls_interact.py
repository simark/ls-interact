import subprocess
import time
import json
import threading
import queue
import signal
import sys
import os
import select
import argparse


def start_clangd(clangd, compile_commands_dir, run_synchronously=True):
    ''' Start clangd, return a Popen object. '''

    if not clangd:
        clangd = 'clangd'
    
    cmd = '{}'.format(clangd)

    if run_synchronously:
        cmd += ' -run-synchronously'

    if compile_commands_dir:
        cmd += ' -compile-commands-dir=' + compile_commands_dir

    return subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE)


class JsonRpc:
    class JsonRpcPendingId:
        def __init__(self, the_id):
            self._id = the_id

        def matches(self, json_data):
            return 'id' in json_data and json_data['id'] == self._id

        def extract(self, json_data):
            return json_data['result']

    class JsonRpcPendingMethod:
        def __init__(self, method_name):
            self._method_name = method_name

        def matches(self, json_data):
            return 'method' in json_data and json_data['method'] == self._method_name

        def extract(self, json_data):
            return json_data['params']

    def __init__(self, output, inp):
        self._output = output
        self._next_id = 123
        self._input = inp

    def request(self, req):
        method_name = req.get_method_name()
        params = req.get_params()

        obj = {}

        obj['jsonrpc'] = '2.0'
        the_id = self._next_id
        obj['id'] = the_id
        self._next_id += 1
        obj['method'] = method_name
        obj['params'] = params

        b = json.dumps(obj).encode()
        header = 'Content-Length: {}\r\n\r\n'.format(len(b)).encode()

        self._output.write(header)
        self._output.write(b)
        self._output.flush()

        return JsonRpc.JsonRpcPendingId(the_id)

    def notify(self, notif):
        method_name = notif.get_method_name()
        params = notif.get_params()

        obj = {}

        obj['jsonrpc'] = '2.0'
        obj['method'] = method_name
        obj['params'] = params

        b = json.dumps(obj).encode()
        header = 'Content-Length: {}\r\n\r\n'.format(len(b)).encode()

        self._output.write(header)
        self._output.write(b)
        self._output.flush()

    def pull_one_message(self):
        buf = b""

        while True:
            buf += self._input.read(1)

            if buf.endswith(b'\r\n\r\n'):
                content_length = -1

                headers = buf.split(b'\r\n')
                for h in headers:
                    if h.startswith(b'Content-Length: '):
                        content_length = int(h[len(b'Content-Length: '):])

                assert content_length > 0

                buf = self._input.read(content_length)

                assert len(buf) == content_length

                json_data = json.loads(buf.decode())

                return json_data

    def wait_for(self, pending):
        while True:
            json_data = self.pull_one_message()
            if pending.matches(json_data):
                return pending.extract(json_data)


class Base:

    def __init__(self, method_name):
        self._method_name = method_name

    def get_method_name(self):
        return self._method_name


class Initialize(Base):

    def __init__(self):
        super().__init__('initialize')

    def get_params(self):
        return {}


class Shutdown(Base):

    def __init__(self):
        super().__init__('shutdown')

    def get_params(self):
        return {}


class Exit(Base):

    def __init__(self):
        super().__init__('exit')

    def get_params(self):
        return {}


class DidOpenTextDocument(Base):

    def __init__(self, path):
        super().__init__('textDocument/didOpen')
        self._path = path

    def get_params(self):
        with open(self._path) as f:
            data = f.read()

        obj = {}
        obj['textDocument'] = {}
        obj['textDocument']['uri'] = 'file://' + self._path
        obj['textDocument']['languageId'] = 'cpp'
        obj['textDocument']['version'] = 1
        obj['textDocument']['text'] = data
#        obj['metadata'] = {}
#        obj['metadata']['extraFlags'] = ['-xc++']

        return obj


class GotoDefinition(Base):

    def __init__(self, path, line, col):
        super().__init__('textDocument/definition')
        self._path = path
        self._line = line
        self._col = col

    def get_params(self):
        obj = {}

        obj['textDocument'] = {}
        obj['textDocument']['uri'] = 'file://' + self._path
        obj['position'] = {}
        obj['position']['line'] = self._line - 1
        obj['position']['character'] = self._col - 1

        return obj


class DidChangeConfiguration(Base):

    def __init__(self, new_compile_commands_dir):
        super().__init__('workspace/didChangeConfiguration')
        self._new_compile_commands_dir = new_compile_commands_dir

    def get_params(self):
        obj = {}
        obj['settings'] = {}
        obj['settings']['compilationDatabasePath'] = self._new_compile_commands_dir
        return obj


def run(callback):
    argparser = argparse.ArgumentParser()
    argparser.add_argument('--compile-commands-dir',
                           help='directory containing the compile_commands.json')
    argparser.add_argument('--clangd',
                           help='clangd executable')
    args = argparser.parse_args()

    clangd = start_clangd(args.clangd, args.compile_commands_dir, run_synchronously=False)
    json_rpc = JsonRpc(clangd.stdin, clangd.stdout)

    p = json_rpc.request(Initialize())
    r = json_rpc.wait_for(p)

    callback(json_rpc)
    
    p = json_rpc.request(Shutdown())
    r = json_rpc.wait_for(p)

    json_rpc.notify(Exit())

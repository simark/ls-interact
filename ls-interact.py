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

# Start clangd, return a Popen object.


def start_clangd(clangd, compile_commands_dir):
    if not clangd:
        clangd = 'clangd'

    cmd = '{} -run-synchronously'.format(clangd)

    if compile_commands_dir:
        cmd += ' -compile-commands-dir=' + compile_commands_dir

    return subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE)


class ReceiveThread(threading.Thread):
    def __init__(self, inp, recv_queue):
        super().__init__()
        self._input = inp
        self._recv_queue = recv_queue

    def run(self):
        buf = b""

        while True:
            buf += self._input.read(1)

            idx = buf.find(b'\r\n\r\n')
            if idx >= 0:
                header = buf[:idx + 4]
                buf = buf[idx + 4:]
                content_length = -1

                headers = header.split(b'\r\n\r\n')
                for h in headers:
                    if h.startswith(b'Content-Length: '):
                        content_length = int(h[len(b'Content-Length: '):])

                to_read = max(content_length - len(buf), 0)

                buf += self._input.read(to_read)

                assert len(buf) >= content_length

                json_data = buf[:content_length]
                buf = buf[content_length:]
                json_data = json_data.decode()
                json_data = json.loads(json_data)

                self._recv_queue.put(json_data)


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
        self._recv_queue = queue.Queue()
        self._recv_thread = ReceiveThread(inp, self._recv_queue)
        self._recv_thread.start()

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

    def wait_for(self, pending):
        while True:
            json_data = self._recv_queue.get()
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


def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument('--compile-commands-dir',
                           help='directory containing the compile_commands.json')
    argparser.add_argument('--clangd',
                           help='clangd executable')
    args = argparser.parse_args()

    clangd = start_clangd(args.clangd, args.compile_commands_dir)
    json_rpc = JsonRpc(clangd.stdin, clangd.stdout)

    p = json_rpc.request(Initialize())
    r = json_rpc.wait_for(p)

    # sys.stdin.readline()

    path = '/home/emaisin/src/binutils-gdb/gdb/osdata.c'

    p = json_rpc.notify(DidOpenTextDocument(path))
    r = json_rpc.wait_for(JsonRpc.JsonRpcPendingMethod(
        'textDocument/publishDiagnostics'))

    p = json_rpc.request(GotoDefinition(path, 178, 15))
    r = json_rpc.wait_for(p)

    p = json_rpc.request(Shutdown())
    r = json_rpc.wait_for(p)

    json_rpc.notify(Exit())

    os._exit(0)


try:
    main()
except KeyboardInterrupt:
    os._exit(1)

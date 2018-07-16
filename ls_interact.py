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
import common

from colorama import Fore, Back, Style
from pygments import highlight
from pygments.lexers import JsonLexer
from pygments.formatters import TerminalFormatter


def print_log(json_bytes, sender, log_pretty):
    assert type(json_bytes) == bytes
    assert sender == 'client' or sender == 'server'

    j = json_bytes.decode('utf-8')

    if log_pretty:
        j = json.dumps(json.loads(j), indent=4)

    if sender == 'client':
        prefix = 'client --> server'
        back = Back.GREEN
    else:
        prefix = 'server --> client'
        back = Back.BLUE

    j = highlight(j, JsonLexer(), TerminalFormatter())
    print('{}{}{}{}: {}'.format(back, Fore.BLACK, prefix, Style.RESET_ALL, j))


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

    def __init__(self, output, inp, log, log_pretty):
        self._output = output
        self._next_id = 123
        self._input = inp
        self._log = log
        self._log_pretty = log_pretty

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
        if self._log:
            print_log(b, 'client', self._log_pretty)

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
        if self._log:
            print_log(b, 'client', self._log_pretty)

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

                if self._log:
                    print_log(buf, 'server', self._log_pretty)

                json_data = json.loads(buf.decode())

                return json_data

    def wait_for(self, pending):
        while True:
            json_data = self.pull_one_message()
            if pending.matches(json_data):
                return pending.extract(json_data)


class Range:

    def __init__(self, start_line, start_col, end_line, end_col):
        self._sl = start_line
        self._sc = start_col
        self._el = end_line
        self._ec = end_col

    def to_lsp(self):
        return {
            'start': {
                'line': self._sl - 1,
                'character': self._sc - 1,
            },
            'end': {
                'line': self._el - 1,
                'character': self._ec - 1,
            },
        }

    @property
    def lsp_start_line(self):
        return self._sl - 1

    @property
    def lsp_start_col(self):
        return self._sc - 1

    @property
    def lsp_end_line(self):
        return self._el - 1

    @property
    def lsp_end_col(self):
        return self._ec - 1


class Base:

    def __init__(self, method_name):
        self._method_name = method_name

    def get_method_name(self):
        return self._method_name


class Initialize(Base):

    def __init__(self, params):
        super().__init__('initialize')
        self._params = params

    def get_params(self):
        return self._params


class Initialized(Base):

    def __init__(self):
        super().__init__('initialized')

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


class DidCloseTextDocument(Base):

    def __init__(self, path):
        super().__init__('textDocument/didClose')
        self._path = path

    def get_params(self):
        obj = {}
        obj['textDocument'] = {}
        obj['textDocument']['uri'] = 'file://' + self._path
        return obj
        

class DidChangeTextDocument(Base):

    def __init__(self, path, text):
        super().__init__('textDocument/didChange')
        self._path = path
        self._text = text

    def get_params(self):
        obj = {}
        obj['textDocument'] = {}
        obj['textDocument']['uri'] = 'file://' + self._path
        obj['contentChanges'] = [{
            'text': self._text,
        }]
        
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


class CodeLens(Base):

    def __init__(self, path):
        super().__init__('textDocument/codeLens')
        self._path = path

    def get_params(self):
        obj = {}

        obj['textDocument'] = {}
        obj['textDocument']['uri'] = 'file://' + self._path

        return obj


class CodeLensResolve(Base):

    def __init__(self, lens):
        super().__init__('codeLens/resolve')
        self._lens = lens

    def get_params(self):
        return self._lens


class CodeAction(Base):

    def __init__(self, path, range_, diags):
        super().__init__('textDocument/codeAction')
        self._path = path
        if type(range_) == Range:
            self._range = range_.to_lsp()
        else:
            self._range = range_
        self._diags = diags

    def get_params(self):
        obj = {}

        obj['textDocument'] = {}
        obj['textDocument']['uri'] = 'file://' + self._path
        obj['range'] = self._range
        obj['context'] = {
            'diagnostics': self._diags,
        }

        return obj


class Hover(Base):

    def __init__(self, path, line, col):
        super().__init__('textDocument/hover')
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

    def __init__(self, params):
        super().__init__('workspace/didChangeConfiguration')
        self._params = params

    def get_params(self):
        return self._params
        

class WorkspaceSymbol(Base):

    def __init__(self, query):
        super().__init__('workspace/symbol')
        self._query = query

    def get_params(self):
        return {
            'query': self._query
        }
        


def run(callback, initialize_params={}):
    argparser = argparse.ArgumentParser()
    argparser.add_argument('server',
                           help='server executable (may contain additional args)')
    argparser.add_argument('--log', action='store_true',
                           help='print communication with the server')
    argparser.add_argument('--log-pretty', action='store_true',
                           help='when --log is enabled, pretty-print the json')
    args = argparser.parse_args()

    server = common.start_tool(args.server)
    json_rpc = JsonRpc(server.stdin, server.stdout, args.log, args.log_pretty)

    p = json_rpc.request(Initialize(initialize_params))
    r = json_rpc.wait_for(p)

    json_rpc.notify(Initialized())

    callback(json_rpc)

    p = json_rpc.request(Shutdown())
    r = json_rpc.wait_for(p)

    json_rpc.notify(Exit())

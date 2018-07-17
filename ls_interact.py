import argparse
import common
from common import Base


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
                           help=('server executable (may contain additional ' +
                                 'args)'))
    argparser.add_argument('--log', action='store_true',
                           help='print communication with the server')
    argparser.add_argument('--log-pretty', action='store_true',
                           help='when --log is enabled, pretty-print the json')
    args = argparser.parse_args()

    server = common.start_tool(args.server)
    json_rpc = common.JsonRpc(server.stdin, server.stdout, args.log,
                              args.log_pretty)

    p = json_rpc.request(common.Initialize(initialize_params))
    json_rpc.wait_for(p)

    json_rpc.notify(Initialized())

    callback(json_rpc)

    p = json_rpc.request(Shutdown())
    json_rpc.wait_for(p)

    json_rpc.notify(Exit())

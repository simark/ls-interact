import subprocess
import json

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


def start_tool(langserv):
    ''' Start the language server, return a Popen object. '''

    cmd = '{}'.format(langserv)
    return subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE)


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
            return ('method' in json_data
                    and json_data['method'] == self._method_name)

        def extract(self, json_data):
            return json_data['params']

    def __init__(self, output, inp, log, log_pretty):
        self._output = output
        self._next_id = 123
        self._input = inp
        self._log = log
        self._log_pretty = log_pretty

    def encodeRequest(self, the_id, method_name, params):
        obj = {}
        obj['jsonrpc'] = '2.0'
        obj['id'] = the_id
        obj['method'] = method_name
        obj['params'] = params
        return obj

    def request(self, req):
        method_name = req.get_method_name()
        params = req.get_params()

        the_id = self._next_id
        self._next_id += 1
        obj = self.encodeRequest(the_id, method_name, params)

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


class Base:

    def __init__(self, method_name):
        self._method_name = method_name

    def get_method_name(self):
        return self._method_name

import common
import argparse
import os
from common import Base


class DebugAdapterPendingId:
    def __init__(self, the_id):
        self._id = the_id

    def matches(self, json_data):
        return ('request_seq' in json_data and
                json_data['request_seq'] == self._id)

    def extract(self, json_data):
        if 'body' not in json_data:
            return {}

        return json_data['body']


class DebugAdapterTransport(common.JsonRpc):
    def encodeRequest(self, this_id, method_name, params):
        obj = {}

        obj['seq'] = this_id
        obj['type'] = 'request'
        obj['command'] = method_name
        obj['arguments'] = params

        return obj

    def pending_id(self, the_id):
        return DebugAdapterPendingId(the_id)


class Initialize(Base):

    def __init__(self):
        super().__init__('initialize')

    def get_params(self):
        return {
            'adapterID': 'da_interact',
            'pathFormat': 'path',
        }


class Launch(Base):

    def __init__(self, target):
        super().__init__('launch')
        self._target = target

    def get_params(self):
        return {
            'cwd': os.getcwd(),
            'target': self._target,
        }


class Attach(Base):

    def __init__(self, pid):
        super().__init__('attach')
        self._pid = pid

    def get_params(self):
        return {
            'cwd': os.getcwd(),
            'target': str(self._pid),
        }


class Threads(Base):
    def __init__(self):
        super().__init__('threads')

    def get_params(self):
        return {}


class StackTrace(Base):
    def __init__(self, thread_id):
        super().__init__('stackTrace')
        self._thread_id = thread_id

    def get_params(self):
        return {
            'threadId': self._thread_id,
        }


def run(interact_cb, args_cb=None):
    argparser = argparse.ArgumentParser()
    argparser.add_argument('server',
                           help=('server executable (may contain additional '
                                 + 'args)'))
    argparser.add_argument('--log', action='store_true',
                           help='print communication with the server')
    argparser.add_argument('--log-pretty', action='store_true',
                           help='when --log is enabled, pretty-print the json')
    args_cb(argparser)
    args = argparser.parse_args()

    server = common.start_tool(args.server)
    json_rpc = DebugAdapterTransport(server.stdin, server.stdout, args.log,
                                     args.log_pretty)

    p = json_rpc.request(Initialize())
    json_rpc.wait_for(p)

    # json_rpc.notify(Initialized())

    interact_cb(json_rpc, args)

    # p = json_rpc.request(Shutdown())
    # r = json_rpc.wait_for(p)

    # json_rpc.notify(Exit())

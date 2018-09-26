#
# Run with: python3 test_clangd.py "/path/to/clangd --compile-commands-dir ${PWD}/cpp-test/build-1"
#

import ls_interact as ls
from common import JsonRpc
import os


def interact(json_rpc):

    paths = ['/home/emaisin/src/ls-interact/ifdef-bug-repro/clock.h']

    for p in paths:
        json_rpc.notify(ls.DidOpenTextDocument(p))

    for p in paths:
        json_rpc.wait_for(JsonRpc.JsonRpcPendingMethod(
            'textDocument/publishDiagnostics'))

def main():
    ls.run(interact)


if __name__ == '__main__':
    main()

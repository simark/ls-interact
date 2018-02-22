#
# Run with: python3 test.py /path/to/clangd
#

import ls_interact as ls
import sys
import os


def interact(json_rpc):

    here = os.getcwd()

    paths = [here + '/test.cpp']

    for p in paths:
        json_rpc.notify(ls.DidOpenTextDocument(p))

    for p in paths:
        json_rpc.wait_for(ls.JsonRpc.JsonRpcPendingMethod(
            'textDocument/publishDiagnostics'))

    r = json_rpc.request(ls.Hover(paths[0], 11, 9))
    r = json_rpc.wait_for(r)

    for i in range(5):
        print(file=sys.stderr)

    print(r['contents']['value'])
    for i in range(5):
        print(file=sys.stderr)


def main():
    ls.run(interact)


if __name__ == '__main__':
    main()

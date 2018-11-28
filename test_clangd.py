#
# Run with: python3 test_clangd.py --log --log-pretty "/path/to/clangd --compile-commands-dir ${PWD}/cpp-test/build-1"
#

import ls_interact as ls
from common import JsonRpc
import os


def interact(json_rpc):

    paths = [os.getcwd() + '/cpp-test/src/first.cpp']

    for p in paths:
        json_rpc.notify(ls.DidOpenTextDocument(p))

    for p in paths:
        json_rpc.wait_for(JsonRpc.JsonRpcPendingMethod(
            'textDocument/publishDiagnostics'))

    # ctrl-click on bob()
    r = json_rpc.request(ls.GotoDefinition(paths[0], 13, 3))
    r = json_rpc.wait_for(r)
    assert len(r) == 1
    assert r[0]['uri'].endswith('/first.h')

    # ctrl-click on bar()
    r = json_rpc.request(ls.GotoDefinition(paths[0], 18, 3))
    r = json_rpc.wait_for(r)
    assert len(r) == 1
    # This doesn't work currently, since there's no cross-cu index.  Instead,
    # it goes to the declaration.
    # assert r[0]['uri'].endswith('/second.cpp')
    assert r[0]['uri'].endswith('/second.h')

    # ctrl-click on foo()
    r = json_rpc.request(ls.GotoDefinition(paths[0], 19, 3))
    r = json_rpc.wait_for(r)
    assert len(r) == 1
    assert r[0]['uri'].endswith('/first.cpp')


def main():
    for build in (1, 2):
        ret = os.system('make -C cpp-test/build-{}'.format(build))
        if ret != 0:
            return ret

    ls.run(interact)


if __name__ == '__main__':
    main()

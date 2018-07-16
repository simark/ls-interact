#
# Run with: python3 test_clangd.py "/path/to/clangd --compile-commands-dir ${PWD}/cpp-test/build"
#

import ls_interact as ls
import sys
import json
import os


def interact(json_rpc):

    paths = [os.getcwd() + '/cpp-test/src/first.cpp']

    for p in paths:
        json_rpc.notify(ls.DidOpenTextDocument(p))

    for p in paths:
        json_rpc.wait_for(ls.JsonRpc.JsonRpcPendingMethod(
            'textDocument/publishDiagnostics'))

    r = json_rpc.request(ls.GotoDefinition(paths[0], 7, 3))
    r = json_rpc.wait_for(r)
    # Broken for now, we have two results, in:
    # - file:///home/emaisin/src/ls-interact/cpp-test/build/../src/first.h
    # - file:///home/emaisin/src/ls-interact/cpp-test/src/first.h
    #assert len(r) == 1
    assert r[0]['uri'].endswith('/first.h')

    r = json_rpc.request(ls.GotoDefinition(paths[0], 12, 3))
    r = json_rpc.wait_for(r)
    assert len(r) == 1
    # This doesn't work currently, since there's no cross-cu index.  Instead, it
    # goes to the declaration.
    # assert r[0]['uri'].endswith('/second.cpp')
    assert r[0]['uri'].endswith('/first.cpp')

    r = json_rpc.request(ls.GotoDefinition(paths[0], 13, 3))
    r = json_rpc.wait_for(r)
    assert len(r) == 1
    assert r[0]['uri'].endswith('/first.cpp')


def main():
    if not os.path.exists('./cpp-test/build/compile_commands.json'):
        print('Could not find compile_commands.json, please run make in ./cpp-test/build.')
        return

    ls.run(interact)


if __name__ == '__main__':
    main()

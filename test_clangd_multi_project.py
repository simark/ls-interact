#
# Run with: python3 test_clangd.py --log --log-pretty "/path/to/clangd --compile-commands-dir ${PWD}/cpp-test/build-1"
#

import ls_interact as ls
from common import JsonRpc
import os

root = os.getcwd() + '/multi-project/'

def interact(json_rpc):

    paths = [root + 'source/bar/bar.cpp',
             root + 'source/libfoo/foo.cpp']

    for p in paths:
        json_rpc.notify(ls.DidOpenTextDocument(p))

    for p in paths:
        json_rpc.wait_for(JsonRpc.JsonRpcPendingMethod(
            'textDocument/publishDiagnostics'))

    # ctrl-click on Multiply() in bar.cpp
    r = json_rpc.request(ls.GotoDefinition(paths[0], 6, 21))
    r = json_rpc.wait_for(r)
    # check that the definition in foo.cpp is found
    assert len(r) >= 1
    assert r[0]['uri'].endswith('/foo.cpp')

    # find references to Multiple() in foo.cpp
    r = json_rpc.request(ls.FindReferences(paths[1], 1, 6))
    r = json_rpc.wait_for(r)
    # check that the call site in bar.cpp is found
    found = False
    for ref in r:
        if ref['uri'].endswith('/bar.cpp'):
            found = True
            break
    assert found


def main():
    ret = os.system('cd multi-project && ./setup.sh')
    if ret != 0:
        return ret

    ls.run(interact, cmdline_args='--background-index', initialize_params={
        'rootUri': 'file://' + root + 'source',
        'initializationOptions': {
            'compilationDatabaseMap': [
                {
                    'sourceDir': root + 'source/libfoo',
                    'dbPath': root + 'build/libfoo'
                },
                {
                    'sourceDir': root + 'source/bar',
                    'dbPath': root + 'build/bar'
                }
            ]
        }
    })


if __name__ == '__main__':
    main()

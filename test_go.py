#
# Run with: python3 test_go.py --log "node --inspect /path/to/go-language-server/out/src-vscode-mock/cli.js --stdio"
#

import ls_interact as ls
import sys
import json
import os


def assert_def(r, uri_end, line, col):
    assert r['uri'].endswith(uri_end)
    assert r['range']['start']['line'] == line
    assert r['range']['start']['character'] == col
    assert r['range']['end']['line'] == line
    assert r['range']['end']['character'] == col


def interact(json_rpc):

    paths = [os.getcwd() + '/go-test/test.go']

    for p in paths:
        json_rpc.notify(ls.DidOpenTextDocument(p))

    # We should receive some diagnostic since there's an error in the program.
    r = json_rpc.wait_for(ls.JsonRpc.JsonRpcPendingMethod(
        'textDocument/publishDiagnostics'))

    diags = r['diagnostics']

    r = json_rpc.request(ls.GotoDefinition(paths[0], 30, 13))
    r = json_rpc.wait_for(r)
    assert_def(r, '/test.go', 9, 5)

    r = json_rpc.request(ls.GotoDefinition(paths[0], 33, 13))
    r = json_rpc.wait_for(r)
    assert_def(r, '/test.go', 21, 5)

    r = json_rpc.request(ls.GotoDefinition(paths[0], 36, 13))
    r = json_rpc.wait_for(r)
    assert_def(r, '/other.go', 2, 5)

    r = json_rpc.request(ls.CodeLens(paths[0]))
    r = json_rpc.wait_for(r)

    # One code lens for each function
    assert len(r) == 3

    for lens in r:
        r2 = json_rpc.request(ls.CodeLensResolve(lens))
        r2 = json_rpc.wait_for(r2)

    # Test CodeAction
    r = json_rpc.request(ls.CodeAction(paths[0], ls.Range(1, 1, 41, 0), diags))
    r = json_rpc.wait_for(r)
    assert len(r) == 1
    assert r[0]['command'] == 'go.import.add'
    assert r[0]['title'] == 'import "golang.org/x/tools/godoc"'
    assert len(r[0]['arguments']) == 1
    assert r[0]['arguments'][0] == 'golang.org/x/tools/godoc'


def main():
    ls.run(interact)


if __name__ == '__main__':
    main()

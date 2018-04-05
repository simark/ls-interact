#
# Run with: python3 test_tsserver.py "node /home/emaisin/src/theia/node_modules/typescript-language-server/lib/cli.js --stdio"
#

import ls_interact as ls
import sys
import json
import os


def interact(json_rpc):

    paths = ['/home/emaisin/src/theia/packages/cpp/src/browser/cpp-client-contribution.ts']

    json_rpc.notify(ls.DidChangeConfiguration({
        'settings': {
            'enable': True,
            # 'configFile': '/home/emaisin/src/theia/configs/strict.tslint.json',
            'run': 'onType',
        }
    }))

    for p in paths:
        json_rpc.notify(ls.DidOpenTextDocument(p))
        
    for p in paths:
        diags = json_rpc.wait_for(ls.JsonRpc.JsonRpcPendingMethod(
                    'textDocument/publishDiagnostics'))
        assert len(diags['diagnostics']) == 0
            
    with open(paths[0]) as f:
        content = f.read()
    
    content = '    \n' + content
    
    json_rpc.notify(ls.DidChangeTextDocument(paths[0], content))
    diags = json_rpc.wait_for(ls.JsonRpc.JsonRpcPendingMethod('textDocument/publishDiagnostics'))
    assert len(diags['diagnostics']) == 1
    diag = diags['diagnostics'][0]
    assert diag['range']['start']['line'] == 0
    assert diag['range']['start']['character'] == 0
    assert diag['range']['end']['line'] == 0
    assert diag['range']['end']['character'] == 4
    
    sys.stdin.readline()
    
    r = json_rpc.request(ls.CodeAction(paths[0], diag['range'], diags['diagnostics']))
    r = json_rpc.wait_for(r)
    
    for action in r:
        print(action['title'])

def main():
    if not os.path.exists('./cpp-test/build/compile_commands.json'):
        print('Could not find compile_commands.json, please run make in ./cpp-test/build.')
        return

    ls.run(interact, {
        'rootUri': 'file:///home/emaisin/src/theia',
    })


if __name__ == '__main__':
    main()

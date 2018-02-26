#
# Run with: python3 test_go.py --log "node --inspect /home/emaisin/src/go-language-server/out/src-vscode-mock/cli.js --stdio"
#

import ls_interact as ls
import sys


def interact(json_rpc):

    paths = ['/home/emaisin/src/ls-interact/test.go']

    for p in paths:
        json_rpc.notify(ls.DidOpenTextDocument(p))

    sys.stdin.readline()

    r = json_rpc.request(ls.GotoDefinition(paths[0], 30, 13))
    json_rpc.wait_for(r)

    r = json_rpc.request(ls.GotoDefinition(paths[0], 33, 13))
    json_rpc.wait_for(r)

    sys.stdin.readline()

    r = json_rpc.request(ls.CodeLens(paths[0]))
    r = json_rpc.wait_for(r)

    for lens in r:
        r2 = json_rpc.request(ls.CodeLensResolve(lens))
        json_rpc.wait_for(r2)


def main():
    ls.run(interact)


if __name__ == '__main__':
    main()

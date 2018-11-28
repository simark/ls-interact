#
# This uses the language server from
#   https://github.com/svenefftinge/xtext-lsp-workshop
# The LS listens on port 5007, so start this script with:
#
# $ python3 test_calc.py :5007 --log --log-pretty
#

import ls_interact as ls
from common import JsonRpc


def interact(json_rpc):
    paths = ['/home/emaisin/src/ls-interact/calc/test.calc']

    for p in paths:
        json_rpc.notify(ls.DidOpenTextDocument(p))

    for p in paths:
        json_rpc.wait_for(JsonRpc.JsonRpcPendingMethod(
            'textDocument/publishDiagnostics'))


def main():
    ls.run(interact, {
        'rootUri': 'file:///home/emaisin/src/ls-interact/calc'
    })


if __name__ == '__main__':
    main()

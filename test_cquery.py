#
# Run with: python3 test_cquery.py --log "/path/to/cquery"
#

import ls_interact as ls
import sys
import json
import os


def interact(json_rpc):

    paths = [os.getcwd() + '/cpp-test/src/first.cpp']

    for p in paths:
        json_rpc.notify(ls.DidOpenTextDocument(p))

    print('Press enter when you think indexing is finished...')
    sys.stdin.readline()

    r = json_rpc.request(ls.GotoDefinition(paths[0], 7, 3))
    r = json_rpc.wait_for(r)
    assert len(r) == 1
    assert r[0]['uri'].endswith('/first.h')

    r = json_rpc.request(ls.GotoDefinition(paths[0], 12, 3))
    r = json_rpc.wait_for(r)
    assert len(r) == 1
    assert r[0]['uri'].endswith('/second.cpp')

    r = json_rpc.request(ls.GotoDefinition(paths[0], 13, 3))
    r = json_rpc.wait_for(r)
    assert len(r) == 1
    assert r[0]['uri'].endswith('/first.cpp')


def main():
    if not os.path.exists('./cpp-test/build/compile_commands.json'):
        print('Could not find compile_commands.json, please run make in ./cpp-test/build.')
        return

    ls.run(interact, {
        'initializationOptions': {
            'cacheDirectory': '/tmp/cquery-cache'
        },
        'rootUri': 'file://' + os.getcwd() + '/cpp-test/build',
    })


if __name__ == '__main__':
    main()

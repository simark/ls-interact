#
# To build code-debug:
# 1. git clone https://github.com/WebFreak001/code-debug.git
# 2. cd code-debug && npm install && npm run vscode:prepublish && cd ..
#

#
# To run this script:
# 1. Compile the "loop" program: g++ loop.cpp -o loop -g3 -O0
# 2. Start it and not the pid it outputs: ./loop
# 3. Run the script in another terminal:
#      python3 test_code_debug.py --log --log-pretty "node ./code-debug/out/src/gdb.js" <pid>
#

import da_interact as da
import sys
import os


def interact(rpc, args):
    r = rpc.request(da.Attach(args.pid))
    rpc.wait_for(r)

    r = rpc.request(da.Threads())
    th = rpc.wait_for(r)

    r = rpc.request(da.StackTrace(th['threads'][0]['id']))
    st = rpc.wait_for(r)
    
    for f in st['stackFrames']:
        print('{} {} {}'.format(f['name'], f['line'], f['source']['name']))

def args_cb(argparser):
    argparser.add_argument('pid', type=int)

def main():
    da.run(interact, args_cb)


if __name__ == '__main__':
    main()

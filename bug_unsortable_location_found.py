from ls_interact import *

def interact(json_rpc):

    paths = [
              '/home/emaisin/src/binutils-gdb/gdb/breakpoint.c',
              '/home/emaisin/src/binutils-gdb/gdb/infrun.c',
              '/home/emaisin/src/binutils-gdb/bfd/cache.c',
             ]

    for p in paths:
        json_rpc.notify(DidOpenTextDocument(p))
    
    for p in paths:
        json_rpc.wait_for(JsonRpc.JsonRpcPendingMethod('textDocument/publishDiagnostics'))   

def main():
    run(interact)

if __name__ == '__main__':
    main()

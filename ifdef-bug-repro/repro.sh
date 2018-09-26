clangd -log=verbose -input-style=delimited <<HERE
{"params": {}, "jsonrpc": "2.0", "method": "initialize", "id": 123}
---
{"params": {}, "jsonrpc": "2.0", "method": "initialized"}
---
{"params": {"textDocument": {"text": "#ifndef CORE_CLOCK_H\\n#define CORE_CLOCK_H\\n#include \\"nng_impl.h\\"\\nextern int foo(void);\\n#endif\\n", "version": 1, "uri": "file://`pwd`/clock.h", "languageId": "cpp"}}, "jsonrpc": "2.0", "method": "textDocument/didOpen"}
HERE

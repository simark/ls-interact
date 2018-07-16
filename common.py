import subprocess

def start_tool(langserv):
    ''' Start the language server, return a Popen object. '''

    cmd = '{}'.format(langserv)
    return subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE)

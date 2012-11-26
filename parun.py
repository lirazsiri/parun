#!/usr/bin/python
# 
# Copyright (c) 2012 Liraz Siri <liraz@turnkeylinux.org>
# 
# This file is part of Parun.
# 
# Parun is open source software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of
# the License, or (at your option) any later version.
# 
"""Run commands in parallel in a screen session

Options:
    --name=STR            Name of screen session
    --daemon              Launch screen into background (daemon mode)

    --minheight=LINES     Minimum screen window height (default: 8)
                        
                          If splitting the screen would produce windows shorter
                          than this show a window list instead.

                          Environment variable: PARUN_MINHEIGHT

Example usage:

    # adhoc command line
    cat /etc/passwd | parun "echo hello; echo =====; echo; cat; sleep 10" \\
                            "echo world; echo =====; echo; cat; sleep 10"

    # as an executable
    cat > example << 'EOF'
    #!/usr/bin/env parun
    echo hello; echo =====; echo; cat; sleep 10
    echo world; echo =====; echo; cat; sleep 10
    EOF

    chmod +x ./example
    cat /etc/passwd | ./example

"""
import os
import sys
import getopt

import re

import time
from temp import TempFile
from commands import mkarg
import executil

DEFAULT_MINHEIGHT = 8

class Error(Exception):
    pass

def usage(e=None):
    if e:
        print >> sys.stderr, "error: " + str(e)

    print >> sys.stderr, "Syntax: %s [ -options ] 'cmd1 args' 'cmd2 args' ... " % sys.argv[0]
    print >> sys.stderr, "Syntax: %s [ -options ] path/to/command-list" % sys.argv[0]
    print >> sys.stderr, __doc__.strip()
    sys.exit(1)

def fatal(s):
    print >> sys.stderr, "error: " + str(s)
    sys.exit(1)

def parse_command_list(fpath):
    commands = []
    command = ""
    for line in file(fpath).readlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        if line.endswith('\\'):
            command += line[:-1]
        else:
            command += line
            commands.append(command)
            command = ""

    return commands

def termcap_get_lines():
    buf = executil.getoutput("resize")
    m = re.search('LINES=(\d+)', buf)
    if not m:
        raise Error("can't parse `resize` output")

    return int(m.group(1))

def fmt_screens(commands, stdin=None):
    screens = []
    for command in commands:
        screen = "screen -t %s /bin/bash -c %s" % (mkarg(command), 
                                                   mkarg("cat %s | (%s)" % (stdin.path, command) 
                                                         if stdin else command))
        screens.append(screen)

    return screens

def parun(commands, minheight=DEFAULT_MINHEIGHT, daemon=False, session_name=None):
    if (termcap_get_lines() - len(commands)) / len(commands) >= minheight:
        split = True
    else:
        split = False

    stdin = None
    if not os.isatty(sys.stdin.fileno()):
        stdin = TempFile()
        stdin.write(sys.stdin.read())
        stdin.close()

    # screen wants stdin to be connected to a tty
    os.dup2(sys.stderr.fileno(), sys.stdin.fileno())

    screens = fmt_screens(commands, stdin)
    if split:
        screenrc = "split\nfocus\n".join([ screen + "\n" for screen in screens ])
    else:
        screenrc = "\n".join(screens) + "\n" + "windowlist -b" + "\n"

    screenrc_tmp = TempFile()
    screenrc_tmp.write(screenrc)
    screenrc_tmp.close()

    args = ["-c", screenrc_tmp.path]
    if daemon:
        args += [ "-dm" ]

    if session_name:
        args += [ "-S", session_name ]

    executil.system("screen", *args)
    if daemon:
        time.sleep(1)

def main():
    try:
        opts, args = getopt.gnu_getopt(sys.argv[1:], 'h', ['name=',
                                                           'minheight=',
                                                           'daemon'])
    except getopt.GetoptError, e:
        usage(e)

    if not args:
        usage()

    session_name = None
    daemon = False
    minheight = None

    val = os.environ.get('PARUN_MINHEIGHT')
    if val:
        minheight = int(val)

    for opt, val in opts:
        if opt == '-h':
            usage()

        if opt == '--daemon':
            daemon = True

        if opt == '--minheight':
            minheight = int(val)

        if opt == '--name':
            session_name = val

    if len(args) == 1:
        fpath = args[0]
        if not os.path.exists(fpath):
            fatal("can't read command-list: no such file '%s'" % fpath)

        commands = parse_command_list(fpath)
        if not session_name:
            session_name = os.path.basename(fpath)
    else:
        commands = args

    opts = {}
    for varname in ('minheight', 'daemon', 'session_name'):
        val = locals()[varname]
        if val:
            opts[varname] = val

    parun(commands, **opts)

if __name__=="__main__":
    main()

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
"""Runs commands in parallel in a screen session

Options:
    --name=STR            Name of screen session
    --daemon

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

from temp import TempFile

DEFAULT_MINHEIGHT = 8

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
    daemonize = False
    minheight = int(os.environ.get('PARUN_MINHEIGHT', str(DEFAULT_MINHEIGHT)))

    for opt, val in opts:
        if opt == '-h':
            usage()

        if opt == '--daemon':
            daemonize = True

        if opt == '--minheight':
            minheight = int(val)

        if opt == '--name':
            session_name = val

    if len(args) == 1:
        commands = parse_command_list(args[0])
    else:
        commands = args

if __name__=="__main__":
    main()


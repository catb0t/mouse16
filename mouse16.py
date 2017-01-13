#!/usr/bin/env python3

"""mouse16 - a concatenative stack-based language

Usage: mouse16.py [ -nth ] [ -s | -v ] [ --lib=FILE ] [ SCRIPT... ]

Options:

    -n,        --dry        don't write anything to disk/network
    -t,        --trace      show a detailed, realtime traceback
    -lFILE,    --lib=FILE   load FILE as a library (WIP)
    -s,        --silent     don't print errors or warnings
    -v,        --verbose    log everything
    -h,        --help       print this help & exit
               --version    print the version & filename then exit

Omission of all above arguments will result in reading from STDIN.

Mandatory arguments to long options are mandatory for short options too.
issues, source, contact: github.com/catb0t/mouse16
"""

__version__ = "0.1"

import readline
import os
import sys

import mouseExec

from docopt import docopt

from mouseClutter import *


__all__ = [
    "main",
    "interpret",
    "Stack",
    "Mouse",
    "CaptainHook",
    "LiteralTable",
]

# mostly for self-interpretation and non-self-recursivity
sys.setrecursionlimit(sys.getrecursionlimit() * 3)

# affects underflowerror behaviour and shebang interpretation
_FROMFILE = False
# logging messages use the filename
_FILENAME = "stdin (typewriter)"
# programmatical check if the parser's jumped or not -- used by LiteralTable
_U_READ_AHEAD = False
# only write to tty fds
_DRYRUN = False
# like python -m trace --trace <FILE>
_TRACERT = False
# print nothing except explicit writes
_SILENT = False
# print *everything*
_VERBOSE = False
# over importing string -- also improves performance
DIGITS = frozenset("0123456789.")

def main() -> None:
    """main entry point (hopefully)"""
    global _FROMFILE, _FILENAME, _DRYRUN, _TRACERT, _SILENT, _VERBOSE

    args = docopt.docopt(__doc__, version=__file__ + " " + __version__)

    _DRYRUN  = args["-n"]
    _TRACERT = args["-t"]
    _SILENT  = args["-s"]
    _VERBOSE = args["-v"]

    fnames = args["SCRIPT"]  # type: str

    if len(fnames) == 0:
        interpret(args)

    elif len(fnames) == 1:
        try:
            os.stat(fnames[0])
        except IOError as error:
            print(error,
                "\nstat: cannot stat '" + fnames[0] +
                "': no such file or directory, interpreting using stdio instead\n")
            interpret(args)
            exit(2)
        else:
            _FROMFILE = True
            _FILENAME = fnames[0]
            try:
                filio = open(_FILENAME, 'r')
                prog = list(filio.read())
            finally:
                filio.close()
            mouse.execute(prog)
            exit(0)

    # open multiple files at once
    elif len(fnames) > 1:
        for fname in fnames:
            try:
                os.stat(fname)
            except IOError as error:
                print(error,
                    "\nstat: cannot stat '" + fname +
                    "': no such file or directory")
            else:
                _FROMFILE = True
                _FILENAME = fname
                try:
                    filio = open(_FILENAME, 'r')
                    prog = list(filio.read())
                finally:
                    filio.close()
                mouse.execute(prog)
        exit(0)

def interpret(args) -> None:
    """an interpreter: it reads stdin."""
    print(
        "flags:" + " ".join([
            str(list(args.keys())[i]) + ":" + str(list(args.values())[i])
            for i in range(len(list(args.keys())))
        ]) + "\n", end=""
    )
    print(
        """run \"{} --help\" in your shell for help on {}

        mouse16 interpreter""".format(
            __file__, os.path.basename(__file__)
        )
    )
    shellnum = 0
    while True:
        try:
            line = list(input("\n mouse  " + str(shellnum) + " )  "))
        except KeyboardInterrupt:
            print("\naborted (EOF to exit)")
        except EOFError:
            print("\nbye\n")
            exit(0)
        else:
            shellnum += 1
            mouse.execute(line)


if __name__ == "__main__":
    mouse = mouseExec.Mouse()
    main()

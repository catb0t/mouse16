#!/usr/bin/env python3

# stackoverflow.com questions that helped shape this project:
#
# Crafting impeccable unittests             -- stackoverflow.com/q/34701382
#
# Readable, controllable iterator indicies  -- stackoverflow.com/q/34734137
#
# Code style particulars                    -- stackoverflow.com/q/34746311
#
# Overloading the assignment operator       -- stackoverflow.com/q/34757038
#
# How to Pythonically log nonfatal errors   -- stackoverflow.com/q/26357367
#
# A more Pythonic switch statement   -- stackoverflow.com/a/3828986/4532996
#
# Indexing dictionaries by value    -- stackoverflow.com/a/11632952/4532996
#
# and many more, to which I didn't contribute.

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
"""  # type: str

__version__ = "0.1"  # type: str

import readline
import os
import sys
import warnings
import types
import typing
from typing import Any, Dict, List, Tuple, Union, Iterable, Sequence, Callable
from docopt import docopt

# affects underflowerror behaviour and shebang interpretation
_FROMFILE = False

# logging messages use the filename
_FILENAME = "stdin (typewriter)"

# allows warnings that occur multiple times in a session to be visible
warnings.simplefilter("always")

# programmatical check if the parser's jumped or not -- used by LiteralTable
_JMPD = False

# only write to tty fds
_DRYRUN = False

# like python -m trace --trace <FILE>
_TRACERT = False

# print nothing except explicit writes
_SILENT = False

# print *everything*
_VERBOSE = False

# over importing string
DIGITS = "0123456789."  # type: str

def main() -> None:
    """main entry point (hopefully)"""
    global _FROMFILE, _FILENAME, _DRYRUN, _TRACERT, _SILENT, _VERBOSE

    args = docopt.docopt(__doc__, version=__file__ + " " + __version__)  # type: Dict[str, Any]

    _DRYRUN  = args["-n"]  # type: bool
    _TRACERT = args["-t"]  # type: bool
    _SILENT  = args["-s"]  # type: bool
    _VERBOSE = args["-v"]  # type: bool

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
            _FILENAME = fnames[0]  # type: str
            try:
                filio = open(_FILENAME, 'r')  # type: _io.TextIOWrapper
                prog = list(filio.read())     # type: List[str]
            finally:
                filio.close()
            mouse.execute(prog)
            exit(0)

    elif len(fnames) > 1:
        for fname in fnames:
            try:
                os.stat(fname)
            except IOError as error:
                print(error,
                    "\nstat: cannot stat '" + fname +
                    "': no such file or directory")
            else:
                _FROMFILE = True  # type: bool
                _FILENAME = fname # type: str
                try:
                    filio = open(_FILENAME, 'r')  # type: _io.TextIOWrapper
                    prog = list(filio.read())     # type: List[str]
                finally:
                    filio.close()
                mouse.execute(prog)

def interpret(args: typing.Dict[str, typing.Any]) -> None:
    """an interpreter: it reads stdin."""
    print(
        "flags:" + " ".join([
            str(list(args.keys())[i]) + ":" + str(list(args.values())[i])
            for i in range(len(list(args.keys())))
        ])[:-2] + "\n", end=""
    )
    print(
        """run \"{} --help\" in your shell for help on {}

        mouse16 interpreter (indev)""".format(
            __file__, os.path.basename(__file__)
        )
    )
    shellnum = 0  # type: int
    while True:
        try:
            line = list(input("\nmouse  " + str(shellnum) + " )  "))  # type: List[str]
        except KeyboardInterrupt:
            print("\naborted")
        except EOFError:
            print("\nbye\n")
            exit(0)
        else:
            shellnum += 1
            mouse.execute(line)

# simplistic workers

isnum = lambda num: type(num) in (int, float)

isarr = lambda ary: type(ary) in (list, tuple, dict)

isint = lambda num: type(num) is int

isflt = lambda num: type(num) is float

isstr = lambda stn: type(stn) is str

strsum = lambda s: sum(map(ord, s))

bool2int = lambda val: int(val)

signflip = lambda num: 0 - num

iseven = lambda n: int(n) % 2 == 0

toeven = lambda n: int(n - 1) if not iseven(n) else int(n)

isnone = lambda x: isinstance(x, type(None))

nop = lambda *args: None

# I don't /want/ to pass a tuple to any/all

allof = lambda *args: all([i for i in args])

anyof = lambda *args: any([i for i in args])


def coer(
        obj: object,
        typ: str
    ) -> typing.Any:
    if typ == "num":
        try:
            return float(obj)
        except ValueError:
            # let caller handle exceptions thrown by supplying a non-numeral
            return int(obj)
    elif isinstance(obj, typ):
        return obj
    try:
        return exec(typ + "(" + str(obj) + ")")
    except (ValueError, TypeError, NameError) as error:
        raise BadInternalCallException("junk type coersion", error)


def flt_part(num: float) -> typing.List[int]:
    num = str(num)
    num = num.split(".") if "." in num else [num, 0]
    return [int(num[0]), int(num[1])]


# these are placeholders, don't mind them


class Info(Warning):
    pass


class TypeWarning(Warning):
    pass


class ParseWarning(Warning):
    pass


class RuntimeWarning(Warning):
    pass


class FatalException(Warning):
    pass


class BadInternalCallException(Exception):
    pass


class Stack(object):

    def __init__(self: object) -> None:
        self.__stack__ = []  # type: List[Any]

    def log(self,
            logstring: str,
            errno:     int,
            stklvl:    int = 3
        ) -> None:
        """logging interface for runtime warnings and exceptions"""
        logsdict = {
            0: Info,
            1: TypeWarning,
            2: ParseWarning,
            3: RuntimeWarning,
            4: FatalException
        }
        warnings.warn(logstring, logsdict[errno], stacklevel=stklvl)
        if errno == 4 and _FROMFILE == True:
            raise SystemExit(4)

    def error(self,
            errkey: str
        ) -> None:
        """interface for throwing fatal errors"""
        errors = {
            "zerodiv"       : "attempted to perform integer or float division or modulo by zero",
            "stackunderflow": "stack underflow: not enough operands on stack for <operator>",
            "stackoverflow" : "stack overflow: stack size exceeded memory",
            "recursionerr"  : "call stack exceeded maximum recursion depth"
        }
        self.log(errors[errkey], 4, stklvl=5)


    def nosuchop(self,
            operator: str,
            operands: typing.List[str]
        ) -> None:
        """interface for logging TypeWarnings about interoperand relations"""

        operands = [str(type(i)).split("'")[1] for i in operands]

        message = "undefined operator for operand types:\n\toperator: \
        {}\n\toperands: {} and {}\n".format(
            operator,
            operands[0],
            operands[1],
        )

        self.log(message, 1, stklvl=5)

    def inspect(self: object) -> typing.List[typing.Any]:
        return self.__stack__

    def pop(
            self: object,
            idex: int = (-1)
        ) -> typing.Any:
        """( x -- )
        drop and return an item from the TOS"""
        try:
            return self.__stack__.pop(idex)
        except IndexError:
            self.error("stackunderflow")

    def popn(
            self: object,
            n:    int = 2,
            idx:  int = (-1)
        ) -> typing.Tuple[typing.Any]:
        """( z y x -- )
        drops and returns n items from the stack"""
        x = []  # type: List[Any]
        for i in range(n):
                    y = self.pop(idex=idx)
                    if not isnone(y):
                        x.append(y)
                    else:
                        break
        if len(x) == n:
            return tuple(x)

    def push(
            self: object,
            x:    typing.Any
        ) -> None:
        """( -- x )
        push an item to the stack"""
        try:
            self.__stack__.append(x)
        except (MemoryError, OverflowError):
            self.error("stackoverflow")

    def pushn(
            self: object,
            x:    typing.List[typing.Any]
        ) -> None:
        """( -- y x )
        push n items to the stack"""
        for _, obj in enumerate(x):
            self.push(obj)

    def copy(self: object) -> typing.Any:
        """( y x -- y x x )
        return an item from the the stack without dropping"""
        try:
            return self.__stack__[-1]
        except IndexError:
            self.error("stackunderflow")

    def copyn(
            self: object,
            n:    int = 2
        ) -> typing.List[typing.Any]:
        """( z y x -- z y x z y x )
        return n last items from the stack without dropping"""
        result = self.__stack__[signflip(n):]  # type: typing.List[typing.Any]
        if result == []:
            self.error("stackunderflow")
        return result

    def insert(
            self: object,
            item: typing.Any,
            idex: int
        ) -> None:
        """( z y x -- z b y x )
        add an item to the stack at the given index"""
        try:
            self.__stack__.insert(idex, item)
        except LookupError as error:
            raise BadInternalCallException("junk list index") from error

    def insertn(
            self:  object,
            items: typing.List[typing.Any],
            lidex: int
        ) -> None:
        """( z y x -- z b y x )
        add a list of items to the stack at the given index"""
        iter(items)
        for _, obj in enumerate(items):
            self.insert(lidex, obj)
            lidex += 1

    def remove(
            self: object,
            n:    int
        ) -> None:
        """( x -- )
        remove the nth stack item"""
        try:
            del self.__stack__[n]
        except IndexError as error:
            raise BadInternalCallException("junk list index") from error
        return

    def index(
            self: object,
            n:    int
        ) -> typing.List[typing.Any]:
        """( -- )
        return the nth-last stack item"""
        return self.__stack__[signflip(n)]

    def clean(self: object) -> typing.List[typing.Any]:
        """empty the stack, and return the old stack"""
        stk = self.inspect()[:]
        self.__stack__.clear()
        return stk

    # begin math operators

    def add(self: object) -> None:
        """( y x -- x+y )
        performs binary addition
        if x and y are strings, concatenates strings."""
        y, x = self.popn()
        if anyof(isnone(x), isnone(y)):
            return

        if allof(isstr(x), isstr(y)):
            self.push(x + y)

        elif allof(isstr(x), isnum(y)) or allof(isnum(x), isstr(y)):
            try:
                cr_x, cr_y = coer(x, "num"), coer(y, "num")
            except ValueError:  # one or more of the operands can't be numified
                self.push(str(x) + str(y))
            else:
                self.push(cr_x + cr_y)

        elif allof(isnum(x), isnum(y)):
            self.push(x + y)
        else:
            self.nosuchop("add", [x, y])

    def sub(self: object) -> None:
        """( z y x -- z x-y )
        subtract x from y: perform binary negation
        if x and y are strings,
        remove z occurrences of x from y, or all occurrences if ~z"""
        y, x = self.popn()
        if anyof(isnone(x), isnone(y)):
            return

        if allof(isstr(x), isstr(y)):
            try:
                z = self.pop()
            except SystemExit:
                z = len(x)
            if isnum(z) and int(z) > 0:
                x = x.replace(y, "", z)
            else:
                x = x.replace(y, "")
            self.push(x)

        elif allof(isstr(x), isnum(y)):
            try:
                cr_x = coer(x, "num")
            except ValueError:
                self.push(x[:signflip(y)])
            else:
                self.push(cr_x - y)

        elif allof(isnum(x), isstr(y)):
            try:
                cr_y = coer(y, "num")
            except ValueError:
                self.push(y[:signflip(x)])
            else:
                self.push(cr_y - x)

        elif allof(isnum(x), isnum(y)):
            self.push(x - y)

        else:
            self.nosuchop("sub", [x, y])
        return

    def mlt(self: object) -> None:
        """( y x -- x*y )
        multiply x by y: perform binary multiplication
        if one operand is a string and the other is an integer,
        the string will be copied and catenated onto itself
        if both operands are strings, interleaving will occur"""
        y, x = self.popn()
        if anyof(isnone(x), isnone(y)):
            return

        if allof(isstr(x), isstr(y)):
            self.push("".join(i for j in zip(x, y) for i in j))
        elif (
            allof(isnum(y), isstr(x)) or
            allof(isnum(x), isstr(y)) or
            allof(isnum(x), isnum(y))
        ):
            self.push(x * y)
        else:
            self.nosuchop("mlt", [x, y])


    def dmd(self: object) -> None:
        """( y x --  x/y x%y )
        push x div y, then push x modulo y: perform binary div, then binary mod
        this operator is not yet defined for strings"""
        y, x = self.popn()
        if anyof(isnone(x), isnone(y)):
            return

        if allof(isnum(x), isnum(y)):
            try:
                self.pushn([x % y, x / y])
            except ZeroDivisionError:
                self.error("zerodiv")
        else:
            self.nosuchop("dmd", [x, y])


    def flr(self: object) -> None:
        """( y x -- x//y )
        divide x by y, flooring the result: perform binary floor division
        this operator is not yet defined for strings."""
        y, x = self.popn()
        if anyof(isnone(x), isnone(y)):
            return

        if allof(isnum(x), isnum(y)):
            try:
                self.push(x // y)
            except ZeroDivisionError:
                self.error("zerodiv")
        else:
            self.nosuchop("flr", [x, y])

    def lss(self: object) -> None:
        """( y x -- x<y? )
        push 1 if x is less than y: perform binary ordering"""
        y, x = self.popn()
        if anyof(isnone(x), isnone(y)):
            return

        try:
            self.push(bool2int(x < y))
        except TypeError:
            self.nosuchop("lss", [x, y])
        return

    def gtr(self: object) -> None:
        """( y x -- x>y? )
        push 1 if x is greater than y: perform binary ordering"""
        y, x = self.popn()
        if anyof(isnone(x), isnone(y)):
            return

        try:
            self.push(bool2int(x > y))
        except TypeError:
            self.nosuchop("gtr", [x, y])
        return

    def equ(self: object) -> None:
        """( y x -- x=y? )
        push 1 if x is equal to y: perform equality comparison"""
        y, x = self.popn()
        if anyof(isnone(x), isnone(y)):
            return

        if allof(isnum(x), isnum(y)):
            self.push(bool2int(x == y))

        elif allof(isstr(x), isstr(y)):
            xsum, ysum = strsum(x), strsum(y)
            self.push(bool2int(xsum == ysum))

        elif allof(isnum(x), isstr(y)):
            try:
                cr_y = coer(y, "num")
            except ValueError:
                self.push(bool2int(str(x) == str(y)))
            else:
                self.push(bool2int(float(x) == float(y)))

        elif allof(isstr(x), isnum(y)):
            try:
                cr_x = coer(x, "num")
            except ValueError:
                sum_x = strsum(x)
                self.push(bool2int(sum_x == y))
            else:
                self.push(bool2int(float(x) == float(y)))
        else:
            self.nosuchop("equ", [x, y])

    def neg(self: object) -> None:
        """( x -- -x )
        push the inverse sign of x
        on strings, reverses the string"""
        x = self.pop()
        if isnum(x):
            self.push(signflip(x))
        elif isstr(x) or isarr(x):
            self.push(x[::-1])
        else:
            self.nosuchop("dmd", [x, None])

    # here ends math and begins actual stack operations
    # all of these should be type-agnostic

    def dup(self: object) -> None:
        """( y x -- y x x )
        push a copy of the TOS"""
        self.push(self.copy())

    def dupn(
            self: object,
            n:    int = 2
        ) -> None:
        """( z y x -- z y x y x )
        copy n items from the TOS; push them preserving order"""
        x = self.copyn(n)
        for i in x:
            self.push(i)

    def swap(self: object) -> None:
        """( y x -- x y )
        swap the top two items on the stack"""
        self.pushn(self.popn())

    def rot(self: object) -> None:
        """( z y x w -- z w y x )
        rotates only top three items up"""
        x = self.copyn(3)
        x.insert(0, x.pop())
        for i in x:
            self.pop()
        for i in x:
            self.push(i)

    def urot(self: object) -> None:
        """( z y x w -- z x w y )
        rotates only top three items down"""
        self.insert(self.pop(), -2)

    def roll(self: object) -> None:
        """( z y x -- y x z )
        roll the stack up"""
        self.push(self.pop(0))

    def rolln(
            self: object,
            n:    int = 2
        ) -> None:
        """( z y x -- x z y )
        roll the stack up by n"""
        for i in range(n):
            self.roll()

    def uroll(self: object) -> None:
        """( z y x -- x z y )
        roll the stack down"""
        self.insert(self.pop(), 0)

    def urolln(
            self: object,
            n:    int = 2
        ) -> None:
        """( z y x -- y x z )
        roll the stack down by n"""
        for i in range(n):
            self.uroll()

    def drop(self: object) -> None:
        """( y x -- y )
        silently drops from the stack"""
        self.pop()

    def dropn(
            self: object,
            n:    int = 2
        ) -> None:
        """( y x -- )
        silently drops n items from the stack"""
        self.popn(n)

    def over(self: object) -> None:
        """( z y x -- z y x y )
        copies second-to-top item to TOS"""
        self.push(self.index(2))

    def nip(self: object) -> None:
        """( y x -- x )
        silently drops second-to-top item"""
        self.pop(-2)

    def tuck(self: object) -> None:
        """( y x -- x y x )
        copies TOS behind second-to-top"""
        self.insert(self.copy(), -2)

    # i/o

    def put(
            self:   object,
            *args:  typing.List[typing.Any],
            **kwds: typing.Dict[str, typing.Any]
        ) -> None:
        """( x -- )
        pops the top of the stack and prints/executes"""
        x = self.copy()  # type: Union[Any, Any]
        if isnone(x):
            return
        else:
            self.drop()
            length = sys.stdout.write(str(x))
            del length
        del x

    def emit(
            self:   object,
            *args:  typing.List[typing.Any],
            **kwds: typing.Dict[str, typing.Any]
        ) -> None:
        """( x -- )
        pops the top of the stack and prints that unicode char"""
        x = self.pop()  # type: Union[str, int]
        try:
            x = int(x)
        except TypeError:
            if isnone(x):
                return
            else:
                self.log(str(x) + " is not a valid UTF-8 codepoint", 1)
        else:
            length = sys.stdout.write(chr(x))
            del length
        del x

    def get(self: object) -> None:
        """push a string from stdin until a newline is found"""
        x = input()
        self.push(x)

    def getuntil(self: object) -> None:
        """read stdandard input until the char on the stack is read"""
        x = self.pop()
        if isnone(x):
            return
        toread = chr(x)
        buf = []
        seen_char = False
        nxt_end = False
        while True:
            char = sys.stdin.read(1)
            if not char:
                break
            if char == toread and nxt_end:
                buf.pop()
                break
            else:
                nxt_end = (char == toread)
                buf.append(char)
        self.push("".join(buf))

    # prints a "presentable" representation of the stack

    def reveal(self: object) -> None:
        """prints the entire stack, pleasantly"""
        stack = self.inspect()
        peek = (
            str(stack)
            .replace("[", "{")
            .replace("]", "}")
            .replace(",",  "")
        )
        sys.stdout.write("<{}> {}".format(len(stack), peek[1:len(peek) - 1]))


class CaptainHook(object):
    def __init__(self: object) -> None:
        """allows "hooking" index variable assignment"""
        self.v = (0, None)  # type: Tuple[int, LiteralTable]

    def __eq__(
            self: object,
            o:    object
        ) -> bool:
        if o == self.v:
            return True
        return False

    def __gt__(
            self: object,
            o:    object
        ) -> bool:
        if o > self.v:
            return True
        return False

    def __lt__(
            self: object,
            o:    object
        ) -> bool:
        if o < self.v:
            return True
        return False

    def __setattr__(
            self: object,
            n:    object,
            info: object
        ) -> None:
        value, othercls = info
        if isnum(value):
            global _JMPD
            if isnone(othercls):
                super().__setattr__(n, value)
                return
            elif othercls.tabl.get(value) == True:
                raise BadInternalCallException(
                    "the parser tried to jump inside a string"
                )
            #print("mode of", n, "changed from", self.v, "to", value)
            #print("whether a jump had occurred this cycle changed from", _JMPD, "to True")
            _JMPD = True
            super().__setattr__(n, value)

        else:
            raise TypeError(
                "need an integer not" + str(type(value))
            )

class LiteralTable(object):
    def __init__(self: object) -> None:
        """container for the parser to keep track of all literals in the program
        such that it doesn't try to jump to one."""
        self.tabl  = {}              # type: Dict[int, object]
        self.count = len(self.tabl)  # type: int

    def new(
            self:    object,
            index:   int,
            rangeof: range
        ) -> None:
        """adds an item to the string table
        fails with an error if index exists"""
        if not isinstance(rangeof, range):
            raise TypeError("need a range value not {}".format(
                    type(rangeof)
                )
            )

        if index in self.tabl:
            raise BadInternalCallException(
                "cannot update string #{} at {} to table: string exists".format(
                    str(index), repr(rangeof)
                )
            )
        self.tabl[index] = rangeof  # type: range

    def get(
            self:    object,
            index:   int,
            byrange: int
        ) -> bool:
        """boolean based on query of string table"""
        print("querying string: at", str(index), repr(byrange))
        return anyof(index in self.tabl, byrange in self.tabl.values())

    def __del__(self: object) -> None:
        """immutability!! yay!! doesn't affect garbage collection, though"""
        pass

class Macro(object):
    pass


class Mouse(object):

    def __init__(self: object) -> None:
        """a parser + runner class."""

        self._stack = Stack()

        self._retstk = Stack()


        self.funcdict = {
            "⏏": (nop,                   ()),
            chr(4): (nop,                ()),  # make ^D silent
            "\n": (nop,                  ()),
            "\r": (nop,                  ()),  # windows compatibilty
            " ": (nop,                   ()),  # whitespace needs to be defined
            "\"": (self._lit_string,     ()),  # quotes for strings
            "\'": (self._lit_char,       ()),  # apostrophe pushes nxt charcode
            "_": (self._stack.neg,       ()),  # see method decl.
            "+": (self._stack.add,       ()),
            "-": (self._stack.sub,       ()),
            "*": (self._stack.mlt,       ()),
            "/": (self._stack.dmd,       ()),
            ">": (self._stack.gtr,       ()),
            "<": (self._stack.lss,       ()),
            "=": (self._stack.equ,       ()),
            ",": (self._stack.emit,      ()),  # write charcode on stack
            "?": (self._stack.get,       ()),  # read stdin
            "!": (self._writer,          ()),  # pop something and "do" it
            "@": (self._stack.rot,       ()),  # see method decl.
            "$": (self._stack.dup,       ()),
            "%": (self._stack.swap,      ()),
            "^": (self._stack.over,      ()),
            "&": (self._stack.roll,      ()),
            ";": (self._stack.reveal,    ()),  # show the content of stack
            "`": (self._string_as_mouse, ()),  # execs a string as mouse
            "~": (self._trade_ret_main,  ()),
            "None": (self._retstk.push, (self._stack.pop)),
            "None": (self._stack.push, (self._retstk.pop)),
        } # type: Dict[str, Tuple[object, object]]

        self.funcdict[""] = (self.print_bound, ()) # uses EOT for viewing the function dictionary

    def print_bound(self: object) -> None:
        """ ( -- )
        print a list of currently defined operators and their functions."""
        print(
            "\na list of currently bound functions and operators:\n\n",
            "\n\n".join([
                str(list(self.funcdict.keys())[i])
                + "\t" + str(list(self.funcdict.values())[i][0].__name__)
                + "\n\t" + str(list(self.funcdict.values())[i][0].__doc__)
                for i in range(len(list(self.funcdict.keys())))
                if str(list(self.funcdict.values())[i][0].__doc__) != "None"
                and str(list(self.funcdict.keys())[i]) != "None"
            ])
        )

    def execute(
            self: object,
            proglist: typing.List[str]
        ) -> None:
        """parse and JIT run mouse code"""

        self.toklist = proglist          # type: List[str]

        self.idx       = CaptainHook()
        self.lit_table = LiteralTable()

        self.line = 1
        self.char = 1

        while True:
            global _JMPD
            _JMPD = False

            try:
                self.tok = self.toklist[self.idx.v]

            except IndexError:
                if (
                    len(self._stack.inspect()) > 0
                    and _FROMFILE == True
                ):
                    self._stack.put()
                break

            if self.tok in DIGITS:
                print("found a digit at", str(self.idx.v))
                self._lit_num()
                continue

            elif self.tok in self.funcdict:
                self.func, self.arg = self.funcdict.get(self.tok, nop)
                try:
                    self.func(*self.arg)
                except ValueError as error:
                    raise BadInternalCallException(
                        "junk call, possible bug found"
                    ) from error

            else:
                nodeftupl = (
                    "at char " + str(self.char) + ", line " + str(self.line) +
                    "of file " + _FILENAME + ": ignoring token '" + self.tok +
                    "' which needs a definition before it can be used"
                )
                self._stack.log(nodeftupl, 2)

            if _JMPD == False:
                self.idx.v = (self.idx.v + 1, self.lit_table)

    # end def Mouse.execute

    def _lit_num(self: object) -> None:
        """( -- x )
        catenate each contiguous numeral into a number, then push that"""
        import re
        num_match = re.compile(r"^([.\d]+[.\d]+|[.\d])")
        result = re.match(num_match, "".join(self.toklist[self.idx.v - 1:]))  # type: object

        rangeof = range(self.idx.v, self.idx.v + result.span()[1])
        self.lit_table.new(self.idx.v, rangeof)

        num = result.groups()[0]  # type: object
        num = float(num) if "." in num else int(num)

        self._stack.push(num)

        self.idx.v = (
            self.idx.v + len(str(num)),
            self.lit_table
        )

    def _lit_string(self: object) -> None:
        """ ( "string" --  )
        push everything between unescaped quotes to the stack as a list,
        then update the parser's string table with the range."""
        import re
        # get the string delimiter from the function list
        string_delim = list(self.funcdict.keys())[
                list(self.funcdict.values())
                .index((self._lit_string, ()))]

        # get the string, using the possibly custom delimiter
        expr = re.compile(
            r'{}([^{}\\]*(?:\\.[^{}\\]*)*){}'
            .format(
                string_delim,
                string_delim,
                string_delim,
                string_delim,
            )
        )

        # extract it
        result = re.match(expr, "".join(self.toklist[self.idx.v - 1:]))

        print(result)

        # get its expanse
        rangeof = range(self.idx.v, self.idx.v + result.span()[1])

        # add its entry to the table or fail
        self.lit_table.new(self.idx.v, rangeof)

        self._stack.push(result)

        # update the parser's index
        self.idx.v = (
            rangeof[-1],
            self.lit_table
        )

    def _lit_char(self: object) -> None:
        """ ( -- x )
        push the charcode of the next char in the program,
        then tell the parser to skip that char"""
        try:
            self._stack.push(
                ord(self.toklist[
                    self.idx.v + 1]))
        except IndexError:
            self._stack.log(
                "found EOF before character for literal at char " +
                str(self.char + 1) + ", line " + str(self.line) +
                " : file " + _FILENAME, 2
            )
        else:
            self.lit_table.new(self.idx.v, range(1))       # add string to list
            self.idx.v = (self.idx.v + 2, self.lit_table)  # skip next char

    def _writer(self: object) -> None:
        """ ( x -- )
        write something from the stack to sys.stdout
        (WIP)"""
        self._stack.put()

    def _next_inst(
            self: object,
            subs: str,
            atindex: int
        ) -> int:
        """return the next instance of a substring in a string"""
        return(
            "".join(self.toklist[atindex:])
            .find(subs)
            + atindex
            if subs in self.toklist
            else None
        )

    def _string_as_mouse(self: object) -> None:
        """ ( x -- )
        pop a string off the stack and give it to the runner"""
        self.execute(self._stack.pop())

    def _trade_ret_main(self: object) -> None:
        """ ( ? -- ? )
        swap the contents of the main stack with the secondary stack"""
        oldstk = self._stack.clean()   # type: List[Any]
        oldret = self._retstk.clean()  # type: List[Any]

        self._stack.__stack__  = oldret
        self._retstk.__stack__ = oldstk

    # control structs need access to the runner so not defable by Stack()

    def _dofor(self: object) -> None:
        """do something while something else is true"""
        pass

    def _simple_cond(self: object) -> None:
        """pops a quotation as a condition, another to execute if true,
        and another to execute if the condition is false"""
        pass

if __name__ == "__main__":
    mouse = Mouse()
    main()

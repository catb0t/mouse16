#!/usr/bin/env python3

import pprint, readline, os, sys, string, warnings

# affects underflowerror behaviour and shebang interpretation
_fromfile = False

# logging messages use the filename
filename = "stdin (typewriter)"

# allows warnings that occur multiple times in a session to be visible
warnings.simplefilter("always")


def main():
    global _fromfile, filename
    if len(sys.argv) > 1:
        try:
            os.stat(sys.argv[1])
        except IOError as error:
            print(error, "\nstat: cannot stat '" + sys.argv[1] +
                "': no such file or directory, interpreting using stdio instead\n")
            interpret()
            exit(0)
        else:
            _fromfile = True
            filename = sys.argv[1]
            try:
                filio = open(filename, 'r')
                prog = list(filio.read())
            finally:
                filio.close()
            mouse.execute(prog)
            exit(0)
    else:
        interpret()


def interpret():
    print("mouse16 interpreter (indev)\nsee Mouse.__init__() for syntax")
    shellnum = 0
    while True:
        try:
            line = list(input("\nmouse  " + str(shellnum) + " )  "))
        except KeyboardInterrupt as kbint:
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


def coer(obj, typ):
    if typ == "num":
        try:
            return float(obj)
        except ValueError:
            # let caller handle exceptions thrown by supplying a non-numeral
            return int(obj)
    elif isinstance(obj, typ):
        return obj
    try:
        return typ(obj)
    except (ValueError, TypeError, NameError) as error:
        raise BadInternalCallException("junk type coersion", error)


def flt_part(num):
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

    def __init__(self):
        self.__stack__ = []

    def log(self, logstring, errno, stklvl=3):
        """logging interface for runtime warnings and exceptions"""
        logsdict = {
            0: Info,
            1: TypeWarning,
            2: ParseWarning,
            3: RuntimeWarning,
            4: FatalException
        }
        warnings.warn(logstring, logsdict[errno], stacklevel=stklvl)
        if errno == 4 and _fromfile == True:
            raise SystemExit(4)
        return

    def error(self, errkey):
        """interface for throwing fatal errors"""
        errors = {
            "zerodiv"       : "attempted to perform integer or float division or modulo by zero",
            "stackunderflow": "stack underflow: not enough operands on stack for <operator>",
            "stackoverflow" : "stack overflow: stack size exceeded memory",
            "recursionerr"  : "call stack exceeded maximum recursion depth"
        }
        self.log(errors[errkey], 4, stklvl=5)
        return

    def nosuchop(self, operator, operands):
        """interface for logging TypeWarnings about interoperand relations"""

        operands = [str(type(i)).split("'")[1] for i in operands]

        message = "undefined operator for operand types:\n\toperator: \
        {}\n\toperands: {} and {}\n".format(
            operator,
            operands[0],
            operands[1],
        )

        self.log(message, 1, stklvl=5)

    def inspect(self):
        return self.__stack__

    def pop(self, idex=-1):
        """( x -- )
        drop and return an item from the TOS"""
        try:
            return self.__stack__.pop(idex)
        except IndexError:
            self.error("stackunderflow")

    def popn(self, n=2, idx=-1):
        """( z y x -- )
        drops and returns n items from the stack"""
        x = []
        for i in range(n):
                    y = self.pop(idex=idx)
                    if not isnone(y):
                        x.append(y)
                    else:
                        break
        if len(x) == n:
            return tuple(x)
        return (None, None)

    def push(self, x):
        """( -- x )
        push an item to the stack"""
        try:
            self.__stack__.append(x)
        except (MemoryError, OverflowError):
            self.error("stackoverflow")
        return

    def pushn(self, x):
        """( -- y x )
        push n items to the stack"""
        for idx, obj in enumerate(x):
            self.push(obj)
        return

    def copy(self):
        """( y x -- y x x )
        return an item from the the stack without dropping"""
        try:
            return self.__stack__[-1]
        except IndexError:
            self.error("stackunderflow")

    def copyn(self, n=2):
        """( z y x -- z y x z y x )
        return n last items from the stack without dropping"""
        result = self.__stack__[signflip(n):]
        if result == []:
            self.error("stackunderflow")
        return result

    def insert(self, item, idex):
        """( z y x -- z b y x )
        add an item to the stack at the given index"""
        try:
            self.__stack__.insert(idex, item)
        except LookupError as error:
            raise BadInternalCallException("junk list index") from error

    def insertn(self, items, lidex):
        """( z y x -- z b y x )
        add a list of items to the stack at the given index"""
        iter(items)
        for idx, obj in enumerate(items):
            self.insert(lidex, obj)
            lidex += 1

    def remove(self, n):
        """( x -- )
        remove the nth stack item"""
        try:
            del self.__stack__[n]
        except IndexError as error:
            raise BadInternalCallException("junk list index") from error
        return

    def index(self, n):
        """( -- )
        return the nth-last stack item"""
        return self.__stack__[signflip(n)]

    def clean(self):
        """empty the stack, and return the old stack"""
        stk = self.inspect()[:]
        self.__stack__.clear()
        return stk

    # begin math operators

    def add(self):
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
        return

    def sub(self):
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

    def mlt(self):
        """( y x -- x*y )
        multiply x by y: perform binary multilpication
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
        return

    def dmd(self):
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
        return

    def flr(self):
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
        return

    def lss(self):
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

    def gtr(self):
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

    def equ(self):
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

    def neg(self):
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

    def dup(self):
        """( y x -- y x x )
        push a copy of the TOS"""
        self.push(self.copy())

    def dupn(self, n=2):
        """( z y x -- z y x y x )
        copy n items from the TOS; push them preserving order"""
        x = self.copyn(n)
        for i in x:
            self.push(i)

    def swap(self):
        """( y x -- x y )
        swap the top two items on the stack"""
        self.pushn(self.popn())

    def rot(self):
        """( z y x w -- z w y x )
        rotates only top three items up"""
        x = self.copyn(3)
        x.insert(0, x.pop())
        for i in x:
            self.pop()
        for i in x:
            self.push(i)

    def urot(self):
        """( z y x w -- z x w y )
        rotates only top three items down"""
        self.insert(self.pop(), -3)

    def roll(self):
        """( z y x -- y x z )
        roll the stack up"""
        self.push(self.pop(0))

    def rolln(self, n=2):
        """( z y x -- x z y )
        roll the stack up by n"""
        for i in range(n):
            self.roll()

    def uroll(self):
        """( z y x -- x z y )
        roll the stack down"""
        self.insert(self.pop(), 0)

    def urolln(self, n=2):
        """( z y x -- y x z )
        roll the stack down by n"""
        for i in range(n):
            self.uroll()

    def drop(self):
        """( y x -- y )
        silently drops from the stack"""
        self.pop()

    def dropn(self, n=2):
        """( y x -- )
        silently drops n items from the stack"""
        self.popn(n)

    def over(self):
        """( z y x -- z y x y )
        copies second-to-top item to TOS"""
        self.push(self.index(2))

    def nip(self):
        """( y x -- x )
        silently drops second-to-top item"""
        self.pop(self.index(2))

    def tuck(self):
        """( y x -- x y x )
        copies TOS behind second-to-top"""
        self.insert(self.copy(), -2)

    # i/o

    def put(self, *args, **kwargs):
        """( x -- )
        pops the top of the stack and prints/executes"""
        x = self.copy()
        if isnone(x):
            return
        else:
            self.drop()
            length = sys.stdout.write(str(x))
            del length
        del x

    def emit(self, *args, **kwargs):
        """( -- )
        pops the top of the stack and prints that unicode char
        """
        x = self.pop()
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

    def get(self):
        """push a string from stdin until a newline is found"""
        x = input()
        self.push(x)

    def getuntil(self):
        """read stdin until the char on the stack is read"""
        x = self.pop()
        if isnone(x):
            return
        toread = chr(x)
        buf = []
        seen_char = False
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

    def reveal(self):
        stack = self.inspect()
        peek = (
            str(stack)
            .replace("[", "{")
            .replace("]", "}")
            .replace(",",  "")
        )
        sys.stdout.write("<{}> {}".format(len(stack), peek[1:len(peek) - 1]))

class Macro(object):
    pass

class Mouse(object):

    def __init__(self):
        # main data stack
        self._stack = Stack()

        # return stack is optional secondary stack allowing for "return" values
        # you can do math and stuff with the return stack, but you'll need to
        # define your own operators to do that.
        self._retstk = Stack()

        # loop stack is used by loop structs, which are technically concurrent
        # in Forth, the loop stack *is* the return stack; I want to avoid
        # mangling valuable return stack values: I'm not pressed for memory
        self._loopstk = Stack()

        # func dict is functions; can be appended to!
        self.funcdict = {
            chr(4): (nop,                ()),
            "\n": (nop,                  ()),
            "\r": (nop,                  ()),
            " ": (nop,                   ()),
            "_": (self._stack.neg,       ()),
            "+": (self._stack.add,       ()),
            "-": (self._stack.sub,       ()),
            "*": (self._stack.mlt,       ()),
            "/": (self._stack.dmd,       ()),
            ">": (self._stack.gtr,       ()),
            "<": (self._stack.lss,       ()),
            "=": (self._stack.equ,       ()),
            ",": (self._stack.emit,      ()),
            "?": (self._stack.get,       ()),
            "!": (self._writer,          ()),
            "@": (self._stack.rot,       ()),
            "$": (self._stack.dup,       ()),
            "%": (self._stack.swap,      ()),
            "^": (self._stack.over,      ()),
            "&": (self._stack.roll,      ()),
            ";": (self._stack.reveal,    ()),
            "`": (self._string_as_mouse, ()),
            "~": (self._trade_ret_main,  ()),
            "NUL1": (self._retstk.push, (self._stack.pop))
            "NUL2": (self._stack.push, (self._retstk.pop))
        }

        self.funcdict["#"] = pprint.pprint(self.funcdict)

    def execute(self, toklist):
        self.current_buf = ""

        self.iff_list,
        self.whilestk = [], []

        self.line,
        self.char = 1, 1

        self.in_str,
        self.in_quot,
        self.nxt_ischr = False, False, False

        for idx, tok in enumerate(toklist):

            self.char += 1

            # take the current line number, when in files.
            # uses \n because it will (maybe?) also detect \r\n on Windows
            if ord(tok) == 10:
                self.line += 1
                self.char =  1

            # quotations have highest precedence
            if self.in_quot == True:
                if tok == "}":
                    self.in_quot = False
                    self._stack.push(self.quotstk)
                else:
                    self.quotstk.append(tok)

            # pushes charcode of token
            elif self.nxt_ischr == True:
                    self._stack.push(ord(tok))
                    self.nxt_ischr = False

            # string recording
            elif self.in_str == True:
                if tok == "\"":
                    if toklist[idx - 1] == "\\":
                        self.current_buf = self.current_buf[:-1]
                        self.current_buf += "\""
                    else:
                        self._stack.push("".join(self.current_buf))
                        self.in_str = False
                else:
                    self.current_buf += tok

            # *more* string recording.
            elif tok == "\"":
                self.in_str = True

            # numbers
            elif (
                tok in string.digits + "."
                and self.in_str  == False
                and self.in_quot == False
            ):
                self.current_buf += tok
                try:
                    toklist[idx + 1]
                except IndexError:
                    try:
                        if "." in self.current_buf:
                            self.current_buf = float(self.current_buf)
                        else:
                            self.current_buf = int(self.current_buf)

                        self._stack.push(self.current_buf)
                        self.current_buf = ""
                    except ValueError:
                        self._stack.push(0.0)

                else:
                    if toklist[idx + 1] not in string.digits + ".":
                        try:
                            if "." in self.current_buf:
                                self.current_buf = float(self.current_buf)
                            else:
                                self.current_buf = int(self.current_buf)

                            self._stack.push(self.current_buf)
                            self.current_buf = ""
                        except ValueError:
                            self._stack.push(0.0)

            # quotations
            elif tok == "{":
                self.in_quot = True

            # nxtchr is charcode to record
            elif tok == "'":
                self.nxt_ischr = True
                try:
                    toklist[idx + 1]
                except IndexError:
                    self._stack.log(
                        "found EOF before character for literal at char " +
                        str(char + 1) + ", line " + str(line) +
                        " : file " + filename, 2
                    )

            elif tok in self.funcdict:
                self.func, self.arg = self.funcdict.get(tok, nop)
                try:
                    self.func(*self.arg)
                except ValueError as error:
                    raise BadInternalCallException(
                        "junk call found, possible bug") from error

            else:
                nodeftupl = ("at char " + str(self.char) + ", line " + str(self.line) +
                    ": ignoring token '" + tok +
                    "' which needs a definition before it can be used")
                try:
                    toklist[idx + 1]
                except:
                    if tok == ":":
                        pass
                    else:
                        self._stack.log(nodeftupl, 2)
                else:
                    if toklist[idx + 1] == ":":
                        pass
                    else:
                        self._stack.log(nodeftupl, 2)
        else:
            return
    # end def mouse.execute

    # function defs that need access to the runner

    def _writer(self):
        x = self._stack.copy()
        if isinstance(x, Macro):
            self._runfunc()
        elif isnone(x):
            return
        else:
            self._stack.put()

    def _string_as_mouse(self):
        self.execute(self._stack.pop())

    def _trade_ret_main(self):
        oldstk = self._stack.clean()
        oldret = self._retstk.clean()

        self._stack.__stack__  = oldret
        self._retstk.__stack__ = oldstk

    # control structs need access to the runner so not defable by Stack()

    def _dofor(self):
        """do something while something else is true"""
        pass

    def _simple_cond(self):
        """pops a quotation as a condition, another to execute if true,
        and another to execute if the condition is false"""
        pass

    def _doquot(self):
        """pops a quotation, and executes everything inside it"""
        return
        x = self._stack.pop()
        if isnone(x):
            return
        x.__stack__ = [str(i) for i in x.__stack__]
        self.execute(x)

stack = Stack()

mouse = Mouse()

if __name__ == "__main__":
    main()

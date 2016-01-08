#!/usr/bin/env python3

import readline, inspect, os, sys, warnings

_fromfile = False

warnings.simplefilter("always")

def main():
    if len(sys.argv) > 1:
        try:
            os.stat(sys.argv[1])
        except IOError as error:
            print(error, "\nstat: cannot stat '" + sys.argv[1] + "': no such file or directory, interpreting from stdio instead\n")
            interpret()
            exit(0)
        else:
            _fromfile= True
            filio = open(sys.argv[1], 'r')
            prog = list(filio.read())
            filio.close()
            mouse.execute(prog)
            exit(0)
    else:
        interpret()

def interpret():
    print("mouse16 interpreter (v.01:indev)\n")
    shellnum = 0
    while True:
        try:
            line = list(input("\t"))
            shellnum += 1
            mouse.execute(line, shellnum=shellnum)
        except KeyboardInterrupt as kbint:
            print("\naborted")
        except EOFError:
            print("\nbye\n")
            exit(0)

def test():
    try:
        import mousetesting
    except ImportError as error:
        print(error)
        print("\ntesting module not found in search path, ignoring")
        return

    mousetesting.unittest.main()

isnum = lambda num: type(num) in (int, float)

isarr = lambda ary: type(ary) in (list, tuple, dict)

isint = lambda num: type(num) is int

isflt = lambda num: type(num) is float

isstr = lambda stn: type(stn) is str

strsum = lambda s: sum(map(ord, s))

bool2int = lambda val: int(val)

signflip = lambda num: 0 - num

iseven = lambda n: int(n) % 2 == 0

toeven = lambda n: int(n-1) if not iseven(n) else int(n)

allof = lambda *args: all([i for i in args])

anyof = lambda *args: any([i for i in args])

def coer(obj, typ):
    if typ == "num":
        try:
            return float(obj)
        except ValueError:
            try:
                return int(obj)
            except ValueError as error:
                raise BadInternalCallException("junk type coersion", error)

    elif isinstance(obj, typ):
        return obj
    try:
        return typ(obj)
    except (ValueError, TypeError) as error:
        raise BadInternalCallException("junk type coersion", error)

class Info(Warning): pass

class TypeWarning(Warning): pass

class ParseWarning(Warning): pass

class RuntimeWarning(Warning): pass

class FatalException(Warning): pass

class BadInternalCallException(Exception): pass

class Stack(object):

    def __init__(self):
        self.stack = []

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
            "zerodiv"         : "attempted to perform integer or float division or modulo by zero",
            "stackunderflow"  : "stack underflow: not enough operands on stack for operator",
            "stackoverflow"   : "stack overflow: the stack size exceeded its allocation",
            "recursionerr"    : "call stack exceeded maximum recursion depth"
        }
        self.log(errors[errkey], 4, stklvl=5)
        return

    def nosuchop(self, operator, operands):
        operands = [str(type(i)).split("'")[1] for i in operands]
        message = "undefined operator for operand types:\n\toperator: {}\n\toperands: {} and {}\n".format(
            operator,
            operands[0],
            operands[1],
        )
        self.log(message, 1, stklvl=5)

    def inspect(self):
        return self.stack

    def pop(self, idex=-1):
        """( x -- )
        drop and return an item from the TOS"""
        try:
            return self.stack.pop(idex)
        except IndexError:
            self.error("stackunderflow")

    def popn(self, n=2, idx=-1):
        """( z y x -- )
        drops and returns n items from the stack"""
        x = []
        for i in range(n):
                x.append(self.pop(idex=idx))
        return tuple(x)

    def push(self, x):
        """( -- x )
        push an item to the stack"""
        try:
            self.stack.append(x)
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
            return self.stack[-1]
        except IndexError:
            self.error("stackunderflow")
        return

    def copyn(self, n=2):
        """( z y x -- z y x z y x )
        return n last items from the stack without dropping"""
        result = tuple(self.stack[:signflip(n)])
        if result == ():
            self.error("stackunderflow")
        return result

    def insert(self, item, idex):
        """( z y x -- z b y x )
        add an item to the stack at the given index"""
        try:
            self.stack.insert(idex, item)
        except LookupError as error:
            raise BadInternalCallException("junk list index") from error
        return

    def insertn(self, items, lidex):
        """( z y x -- z b y x )
        add a list of items to the stack at the given index"""
        iter(items)
        for idx, obj in enumerate(items):
            self.insert(lidex, obj)
            lidex += 1
        return

    def remove(self, n):
        """( x -- )
        remove the nth stack item"""
        try:
            del self.stack[n]
        except IndexError as error:
            raise BadInternalCallException("junk list index") from error
        return

    def index(self, n):
        """( -- )
        return the nth-last stack item"""
        return self.stack[signflip(n)]

    def clean(self):
        """empty the stack, and return the old stack"""
        stk = self.inspect()[:]
        self.stack.clear()
        return stk

    # begin math operators

    def add(self):
        """( y x -- x+y )
        performs binary addition
        if x and y are strings, concatenates strings."""
        y, x = self.popn()
        if allof(isstr(x), isstr(y)):
            self.push(x + y)
        elif allof(isstr(x), isnum(y)) or allof(isstr(y), isnum(y)):
            try:
                cr_x, cr_y = coer(x, "num"), coer(y, "num")
                if allof(isnum(cr_x), isnum(cr_y)):
                    self.push(cr_x + cr_y)
                else:
                    self.push(str(x) + str(y))
            except BadInternalCallException:
                self.push(str(x) + str(y))

        elif allof(isnum(x), isnum(y)):
            self.push(x + y)
        else:
            self.nosuchop("add", [x, y])
        return

    def sub(self):
        """( z y x -- z x-y )
        subtract x from y: perform binary negation
        if x and y are strings, remove z occurrences of x from y, or all occurrences if ~z"""
        y, x = self.popn()
        if allof(isstr(x), isstr(y)):
            z = self.pop()
            if isnum(z) and int(z) > 0:
                x = x.replace(y, "", z)
            else:
                x = x.replace(y, "")
            self.push(x)

        elif allof(isstr(x), isnum(y)) or allof(isstr(y), isnum(y)):
            try:
                cr_x, cr_y = coer(x, "num"), coer(y, "num")
                if allof(isnum(cr_x), isnum(cr_y)):
                    self.push(cr_x - cr_y)
                else:
                    self.push(str(x).replace(y, ""))
            except BadInternalCallException:
                self.push(x[:signflip(y)])

        elif allof(isnum(x), isnum(y)):
            self.push(x - y)
        else:
            self.nosuchop("sub", [x, y])
        return

    def mlt(self):
        """( y x -- x*y )
        multiply x by y: perform binary multilpication
        if one operand is a string and the other is an integer, the string will be copied and catenated onto itself
        if both operands are strings, interleaving will occur"""
        y, x = self.popn()
        if allof(isstr(x), isstr(y)):
            self.push("".join(i for j in zip(s1, s2) for i in j))
        elif anyof(allof(isnum(x), isstr(y)), allof(isstr(y), isnum(x))) \
        or   allof(isnum(x), isnum(y)):
            self.push(x * y)
        else:
            self.nosuchop("mlt", [x, y])
        return

    def dmd(self):
        """( y x --  x/y x%y )
        push x div y, then push x modulo y: perform binary div, then binary mod
        this operator is not yet defined for strings"""
        y, x = self.popn()
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
        push 1 if x is less than y: perform binary ordering
        """
        y, x = self.popn()
        try:
            self.push(bool2int(x < y))
        except TypeError:
            self.nosuchop("lss", [x, y])
        return

    def gtr(self):
        """( y x -- x>y? )
        push 1 if x is greater than y: perform binary ordering
        """
        y, x = self.popn()
        try:
            self.push(bool2int(x > y))
        except TypeError:
            self.nosuchop("gtr", [x, y])
        return

    def equ(self):
        """( y x -- x=y? )
        push 1 if x is equal to y: perform equality comparison
        """
        y, x = self.popn()
        if allof(isnum(x), isnum(y)):
            self.push(bool2int(x == y))
        elif allof(isstr(x), isstr(y)):
            xsum, ysum = strsum(x), strsum(y)
            self.push(bool2int(xsum == ysum))
        elif allof(isnum(x), isstr(y)) or allof(isstr(y), isnum(x)):
            self.push(bool2int(str(x) == str(y)) or bool2int(float(x) == float(y)))
        else:
            self.nosuchop("equ", [x, y])
        return

    # here ends math and begins actual stack operations
    # all of these should be type-agnostic

    def dup(self):
        """( y x -- y x x )
        copy the item on the TOS, then push it"""
        self.push(self.copy())
        return

    def dupn(self, n=2):
        """( z y x -- z y x y x )
        copy n items from the TOS; push them preserving order"""
        self.pushn(self.copyn(n))
        return

    def swap(self):
        """( y x -- x y )
        swap the top two items on the stack"""
        self.pushn(reversed(self.popn()))
        return

    def rot(self):
        """( z y x w -- z w y x )
        rotates only top three items up"""
        self.push(self.copy(-3))
        self.remove(-3)
        return

    def urot(self):
        """( z y x w -- z x w y )
        rotates only top three items down"""
        self.insert(self.pop(), -3)
        return

    def roll(self):
        """( z y x -- y x z )
        roll the stack up"""
        self.push(self.pop(0))
        return

    def rolln(self, n=2):
        """( z y x -- x z y )
        roll the stack up by n"""
        for i in range(n):
            self.rot()
        return

    def uroll(self):
        """( z y x -- x z y )
        roll the stack down"""
        self.insert(self.pop())
        return

    def urolln(self, n=2):
        """( z y x -- y x z )
        roll the stack down by n"""
        for i in range(n):
            self.urot()
        return

    def drop(self):
        """( y x -- y )
        silently drops from the stack"""
        self.pop()
        return

    def dropn(self, n=2):
        """( y x -- )
        silently drops n items from the stack"""
        self.popn(n)
        return

    def over(self):
        """( z y x -- z y x y )
        copies second-to-top item to TOS"""
        self.push(self.index(2))
        return

    def nip(self):
        """( y x -- x )
        silently drops second-to-top item"""
        self.pop(self.index(2))
        return

    def tuck(self):
        """( y x -- x y x )
        copies TOS behind second-to-top"""
        self.insert(self.copy(), -2)
        return

class Mouse(object):
    def __init__(self):
        # main data stack can hold all types
        self.stack    = Stack()

        # return stack is optional secondary stack allowing for "return" values
        self.retstack = Stack()

        # memory tape is dynamically growable, addressable memory
        self.memory   = [0] * 10

        # var dict is variables
        self.vardict  = {}

        # func dict holds macros
        self.funcdict = {}

    def execute(self, toklist, shellnum=None):
        pass

stack = Stack()

mouse = Mouse()

if __name__ == "__main__":
    main()

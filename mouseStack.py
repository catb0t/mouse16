#!/usr/bin/env python3

from mouseClutter import *

import warnings
import sys


from mouse16 import _FROMFILE


# allows warnings that occur multiple times in a session to be visible
warnings.simplefilter("always")


class Info(Warning):
    """
    placeholder class for displaying messages to the user
    """
    pass


class TypeWarning(Warning):
    """
    for warning about incompatible or ambiguous type interactions
    """
    pass


class ParseWarning(Warning):
    """
    warnings about syntax errors like EOL before end of literal
    """
    pass


class RuntimeWarning(Warning):
    """
    warnings that things may not work properly due to certain circumstances
    """
    pass


class FatalException(Warning):
    """
    fatal errors that make continuing to run impossible
    """
    pass


class BadInternalCallException(Exception):
    """
    actually-fatal exceptions about probable bugs in Mouse/this program
    """
    pass


class Stack(object):

    def __init__(self: object):
        self.__stack__ = []

    def log(self, logstring, errno, stklvl = 3):
        """logging interface for runtime warnings and exceptions"""
        logsdict = {
            0: Info,
            1: TypeWarning,
            2: ParseWarning,
            3: RuntimeWarning,
            4: FatalException
        }
        warnings.warn(logstring, logsdict[errno], stacklevel=stklvl)
        if errno == 4 and _FROMFILE:
            raise SystemExit(4)

    def error(self, errkey):
        """interface for throwing fatal errors"""
        errors = {
            "zerodiv"       : "attempted to perform integer or float division or modulo by zero",
            "stackunderflow": "stack underflow: not enough operands on stack for <operator>",
            "stackoverflow" : "stack overflow: stack size exceeded memory",
            "recursionerr"  : "call stack exceeded maximum recursion depth"
        }
        self.log(errors[errkey], 4, stklvl=5)


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

    def pop(self, idex = (-1)):
        """( x -- )
        drop and return an item from the TOS"""
        try:
            return self.__stack__.pop(idex)
        except IndexError:
            self.error("stackunderflow")

    def popn(self, n = 2, idx = (-1)):
        """( z y x -- )
        drops and returns n items from the stack"""
        x = []  # type: List[Any]
        for _ in range(n):
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

    def pushn(self, x):
        """( -- y x )
        push n items to the stack"""
        for _, obj in enumerate(x):
            self.push(obj)

    def copy(self):
        """( y x -- y x x )
        return an item from the the stack without dropping"""
        try:
            return self.__stack__[-1]
        except IndexError:
            self.error("stackunderflow")

    def copyn(self, n = 2):
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
        for _, obj in enumerate(items):
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
                coer(y, "num")
            except ValueError:
                self.push(bool2int(str(x) == str(y)))
            else:
                self.push(bool2int(float(x) == float(y)))

        elif allof(isstr(x), isnum(y)):
            try:
                coer(x, "num")
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

    def dupn(self, n = 2):
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
        for _ in x:
            self.pop()
        for i in x:
            self.push(i)

    def urot(self):
        """( z y x w -- z x w y )
        rotates only top three items down"""
        self.insert(self.pop(), -2)

    def roll(self):
        """( z y x -- y x z )
        roll the stack up"""
        self.push(self.pop(0))

    def rolln(self, n = 2):
        """( z y x -- x z y )
        roll the stack up by n"""
        for _ in range(n):
            self.roll()

    def uroll(self):
        """( z y x -- x z y )
        roll the stack down"""
        self.insert(self.pop(), 0)

    def urolln(self, n = 2):
        """( z y x -- y x z )
        roll the stack down by n"""
        for _ in range(n):
            self.uroll()

    def drop(self):
        """( y x -- y )
        silently drops from the stack"""
        self.pop()

    def dropn(self, n = 2):
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
        self.pop(-2)

    def tuck(self):
        """( y x -- x y x )
        copies TOS behind second-to-top"""
        self.insert(self.copy(), -2)

    # i/o

    def put(self, *args, **kwds):
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

    def emit(self, *args, **kwds):
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

    def get(self):
        """push a string from stdin until a newline is found"""
        x = input()
        self.push(x)

    def get_exact(self):
        """( x -- y )
        get exactly x bytes of stdin, and push them as a string"""
        x = self.pop()
        if isnone(x):
            return
        if not isnum(x):
            CatLogger.Crit("need a number of characters to get not " + repr(type(x)))
            return
        from input_constrain import thismany
        self.push(thismany(x))

    def get_until(self):
        """( x -- y )
        get stdin until the character with codepoint x is read, pushing to y"""
        x = self.pop()
        if isnum(x):
            x = chr(x)
        elif isstr(x):
            x = x[0]
        from input_constrain import until
        self.push(until(x))

    # prints a "presentable" representation of the stack

    def reveal(self):
        """prints the entire stack, pleasantly"""
        stack = self.inspect()
        peek = repr(stack)
        sys.stdout.write("<{}> {}".format(len(stack), peek[1:len(peek) - 1]))

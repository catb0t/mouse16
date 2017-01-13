import mouseStack

from mouseClutter import *

from mouse16 import DIGITS, _FILENAME, _FROMFILE

class CaptainHook(object):
    def __init__(self):
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
            global _U_READ_AHEAD
            if isnone(othercls):
                super().__setattr__(n, value)
                return
            elif othercls.tabl.get(value):
                raise BadInternalCallException(
                    "the parser tried to jump inside a string"
                )
            #print("mode of", n, "changed from", self.v, "to", value)
            #print("whether a jump had occurred this cycle changed from", _U_READ_AHEAD, "to True")
            _U_READ_AHEAD = True
            super().__setattr__(n, value)

        else:
            raise TypeError(
                "need an integer not" + str(type(value))
            )

class LiteralTable(object):
    def __init__(self):
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

    def __del__(self):
        """immutability!! yay!! doesn't affect garbage collection, though"""
        pass

class Mouse(object):

    def __init__(self):
        """a parser + runner class."""

        self._stack = mouseStack.Stack()

        self._retstk = mouseStack.Stack()

        self.funcdict = {
            chr(4): (nop,                ()),  # make ^D silent
            "\n":   (nop,                ()),
            "\r":   (nop,                ()),  # windows compatibilty
            "\"": (self._lit_string,     ()),  # quotes for strings
            "\'": (self._lit_char,       ()),  # apostrophe pushes nxt charcode
            " ":  (nop,                  ()),  # whitespace needs to be defined
            # control structs: double sided
            "[": (self._simple_if,       ()),  # if
            "]": (self._simple_fi,       ()),  # fi
            "(": (self._simple_while,    ()),  # while
            ")": (self._simple_elihw,    ()),  # elihw
            #quotations: not quite the same
            "{": (self._mk_quot,         ()),  # begin quotation
            "}": (self._mk_touq,         ()),  # end
            #goto is a Temporary Replacement for for(;;) and while
            "\\":(self._goto,            ()),
            #misc/other operators
            "_": (self._stack.neg,       ()),  # see method decl.
            "+": (self._stack.add,       ()),
            "-": (self._stack.sub,       ()),
            "*": (self._stack.mlt,       ()),
            "/": (self._stack.dmd,       ()),
            ">": (self._stack.gtr,       ()),
            "<": (self._stack.lss,       ()),
            "=": (self._stack.equ,       ()),
            "?": (self._stack.get,       ()),  # read stdin
            ",": (self._stack.emit,      ()),  # write charcode on stack
            "!": (self._writer,          ()),  # pop something and "do" it
            "@": (self._stack.rot,       ()),  # see method decl.
            "$": (self._stack.dup,       ()),
            "%": (self._stack.swap,      ()),
            "^": (self._stack.over,      ()),
            "&": (self._stack.roll,      ()),
            ";": (self._stack.reveal,    ()),  # show the content of stack
            "`": (self._string_as_mouse, ()),  # execs a string
            "~": (self._trade_ret_main,  ()),
            "None": (self._retstk.push, (self._stack.pop)),
            "None": (self._stack.push, (self._retstk.pop)),
        } # type: Dict[str, Tuple[object, object]]

        self.funcdict["#"] = (self._print_bound_ops, ())

    def _print_bound_ops(self):
        """ ( -- )
        print a list of currently defined operators and their functions."""
        __import__("pydoc").pager(
            "\na list of currently bound functions and operators:\n\n" +
            "\n\n".join([
                str(list(self.funcdict.keys())[i])
                +  "\t"  + str(list(self.funcdict.values())[i][0].__name__)
                + "\n\t" + str(list(self.funcdict.values())[i][0].__doc__)
                for i in range(len(list(self.funcdict.keys())))
                if  str(list(self.funcdict.values())[i][0].__doc__) != "None"
                and str(list(self.funcdict.keys())[i])              != "None"
            ])
        )

    def _get_tokens(self):
        """to make sure we don't accidentally write to the program while it's running.
        as with the Stack(), it's still possible, as is a self-modifying
        implementation but this feels safer"""
        return self.__tokens__

    def execute(self, proglist):
        """parse and JIT run mouse code"""

        try:
            iter(proglist)
        except TypeError as error:
            raise mouseStack.BadInternalCallException(
                "expected an iterable/indexable object not "
                + repr(type(proglist)).split("'")[1]
            ) from error

        self.__tokens__  = [str(i) for i in proglist]
        self.toklist     = self._get_tokens()
        self.__progstr__ = "".join(self.toklist)

        self.idx       = CaptainHook()
        self.lit_table = LiteralTable()

        self.line = 1
        self.char = 1

        # self._condwhile = True  # while loops are true by default

        while True:
            global _U_READ_AHEAD
            _U_READ_AHEAD = False

            self._update_counters()

            try:
                self.tok = self.toklist[self.idx.v]

            except IndexError:
                if (
                    len(self._stack.inspect())
                    and _FROMFILE
                ):
                    self._stack.put()
                break

            if self.tok in DIGITS:
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
                    " of file " + _FILENAME + ": ignoring token '" + self.tok +
                    "' which needs a definition before it can be used"
                )
                self._stack.log(nodeftupl, 2)

            if not _U_READ_AHEAD:
                self.idx.v = (self.idx.v + 1, self.lit_table)

    # end def Mouse.execute

    def _lit_num(self):
        """( -- x )
        catenate each contiguous numeral into a number, then push that"""
        import re
        num_match = re.compile(r"^([.\d]+[.\d]+|[.\d])")
        result = re.match(num_match, "".join(self.toklist[self.idx.v:]))  # type: object
        rangeof = range(self.idx.v, self.idx.v + result.span()[1])
        self.lit_table.new(self.idx.v, rangeof)

        num = result.groups()[0]
        try:
            num = float(num) if "." in num else int(num)
        except ValueError:
            self._stack.push(0.0)

        self._stack.push(num)

        self.idx.v = (
            self.idx.v + len(str(num)),
            self.lit_table
        )

    def _lit_string(self):
        """( -- "string" )
        push everything between unescaped quotes to the stack,
        then update the parser's string table with the range."""
        import re
        # get the string delimiter from the function list
        # using the function whose fingerprint we know
        # to essentially reverse-engineer the function dict
        string_delim = list(self.funcdict.keys())[
                list(self.funcdict.values())
                .index((self._lit_string, ()))]

        # get the string, using the possibly custom delimiter interpolated
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
        result = re.match(expr, "".join(self.toklist[self.idx.v:]))

        # get its expanse
        try:
            rangeof = range(self.idx.v, self.idx.v + result.span()[1])
        except AttributeError:
            return self._stack.log("parser found EOF before closing quote at " + str(self.idx.v), 2, stklvl=4)

        # add its entry to the table or fail
        self.lit_table.new(self.idx.v, rangeof)

        self._stack.push(result.groups()[0])

        # update the parser's index
        self.idx.v = (
            self.idx.v + len(repr(result.groups()[0])),
            self.lit_table
        )

    def _lit_char(self):
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

    def _writer(self):
        """ ( x -- )
        write something from the stack to sys.stdout
        (WIP)"""
        self._stack.put()

    def _next_brace(self, match):
        """walk the program, trying to find a matching brace"""
        depth = 0
        prog  = self.toklist[self.idx.v:]
        if len(match) != 1 or match not in "([{}])":
            raise mouseStack.BadInternalCallException("junk paren type")

        if match in "()":
            group = ["(", ")"]

        elif match in "[]":
            group = ["[", "]"]

        elif match in "{}":
            group = ["{", "}"]

        for i, e in enumerate(prog):
            if e == group[0]:    # found a homogenous opener
                depth += 1

            elif e == group[1]:  # found a homogenous closer
                depth -= 1

            if depth == 0:
                return self.idx.v + i

        self._stack.log(
            "found EOF before matching brace: at char "
            + str(self.char), 2
        )

    def _last_brace(self, match):
        """walk the program in reverse, trying to find a matching brace"""
        depth = 0
        prog  = reversed(self.toklist[:self.idx.v])
        if len(match) != 1 or match not in "([{}])":
            raise BadInternalCallException("junk paren type")

        if match in "()":
            group = ["(", ")"]

        elif match in "[]":
            group = ["[", "]"]

        elif match in "{}":
            group = ["{", "}"]

        for i, e in enumerate(prog):
            if e == group[0]:    # found a homogenous opener
                depth -= 1
            elif e == group[1]:  # found a homogenous closer
                depth += 1

            if depth == 0:
                return self.idx.v - i

        raise BadInternalCallException("junk paren code")

    def _string_as_mouse(self):
        """ ( x -- )
        pop a string off the stack and give it to the runner"""
        prog = self._stack.pop()
        if isstr(prog) and prog.startswith("!!PY!!"):
            try:
                exec(prog[6:])
            except Exception as error:
                print(str(error) + "\n")
            except KeyboardInterrupt:
                pass
            except EOFError:
                return
        else:
            try:
                self.execute(prog)
            except TypeError:
                try:
                    self.execute(list(str(prog)))
                except Exception as error:
                    self._stack.log("tried to exec junk; failed (" + error + ")", 3)

    def _trade_ret_main(self):
        """ ( ? -- ? )
        swap the contents of the main stack with the secondary stack"""
        oldstk = self._stack.clean()   # type: List[Any]
        oldret = self._retstk.clean()  # type: List[Any]

        self._stack.__stack__  = oldret
        self._retstk.__stack__ = oldstk

    def _get_addr(self):
        """readahead and put an address on the stack"""
        self._lit_char()
        addr = self._stack.copy()
        if isnone(addr):
            self._stack.error("stackunderflow")

        elif isint(addr):
            del addr

        elif isstr(addr) and len(addr) == 1:
            self._stack.drop()
            self._stack.push(ord(addr))

        else:
            self._stack.push(int(id(addr)))

    def _update_counters(self):
        """get the current line number and char number on that line"""
        for i, e in enumerate(self.__progstr__):
            if i == self.idx.v:
                break
            if e == "\n":
                self.line += 1
                self.char  = 1
            else:
                self.char += 1

    # basic control flow operators jump around the source somewhat arbitrarily

    def _simple_if(self):
        """IFF
        jumps the pointer around the program based on a condition"""
        cond = self._stack.pop()
        if isnone(cond):
            return
        if bool(cond):
            self.idx.v = (self.idx.v + 1, self.lit_table)
        else:
            nb = self._next_brace("[")
            if isnone(nb):
                return
            self._stack.push(nb)
            self._goto()

    def _simple_fi(self):
        """FFI
        ends a simple conditional (nop/perma-placeholder)
        no relation to semper fi"""
        pass

    def _simple_while(self):
        """WHILE 1
        jumps the pointer back to the opener while the top of the stack is true"""
        print("reached an open brace")

    def _simple_elihw(self):
        """ELIHW
        ends a simple while/for loop (nop/perma-placeholder)"""
        nb = self._last_brace(")")
        if isnone(nb):
            return
        self._stack.push(nb)
        self._goto()

    def _goto(self):
        """( x -- )
        pops an int from the stack and jumps to that char in the source code
        (unless the position is occupied by a literal in the LiteralTable)"""
        whereto = self._stack.pop()
        try:
            whereto = int(float(whereto))
        except (ValueError, TypeError):  # coersion of None to float is a TypeError
            self._stack.log("can't _goto a non-numeral index", 1)
        else:
            self.idx.v = (whereto, self.lit_table)

    # quotation based control structs

    def _mk_quot(self):
        """handle parsing of quotations/lists"""
        pass

    def _mk_touq(self):
        """the end of a quotation/list"""
        pass

    def _new_word(self):
        """pop a quotation and an address to an identifier,
        then assign that identifier to that function in the dict"""
        pass

    def _dofor(self):
        """do something while something else is true"""
        pass

    def _doif(self):
        """pops a quotation as a condition, another to execute if true,
        and another to execute if the condition is false"""
        pass

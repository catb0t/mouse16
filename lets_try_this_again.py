"""the queen, rah, rah"""

class Mouse(object):

    def __init__(self):
        """a parser + runner class."""

        self.toklist = []

        self._stk = Stack()

        self._retstk = Stack()

        self.idx       = CaptainHook()
        self.lit_table = LiteralTable()

        self.line = 1
        self.char = 1

        self.funcdict = {
            "⏏": (nop,                   ()),
            chr(4): (nop,                ()),  # make ^D silent
            "\n": (nop,                  ()),  # newlines shouldn't do anything (unless defined)
            "\r": (nop,                  ()),  # windows compatibilty
            " ": (nop,                   ()),  # whitespace needs to be defined
            "\"": (self._lit_string,     ()),  # quotes for strings
            "\'": (self._lit_char,       ()),  # apostrophe pushes next charcode on stack
            "_": (self._stack.neg,       ()),  # see method decl.
            "+": (self._stack.add,       ()),
            "-": (self._stack.sub,       ()),
            "*": (self._stack.mlt,       ()),
            "/": (self._stack.dmd,       ()),
            ">": (self._stack.gtr,       ()),
            "<": (self._stack.lss,       ()),
            "=": (self._stack.equ,       ()),
            ",": (self._stack.emit,      ()),  # writes the charcode on the stack to stdout
            "?": (self._stack.get,       ()),  # read stdin
            "!": (self._writer,          ()),  # pop something and write it; if executable, call it
            "@": (self._stack.rot,       ()),  # see method decl.
            "$": (self._stack.dup,       ()),
            "%": (self._stack.swap,      ()),
            "^": (self._stack.over,      ()),
            "&": (self._stack.roll,      ()),
            ";": (self._stack.reveal,    ()),  # shows the contents of the stack without modifying
            "`": (self._string_as_mouse, ()),  # execs a string as mouse in the same runner
            "~": (self._trade_ret_main,  ()),
            "placeholder": (self._retstk.push, (self._stack.pop)),
            "placeholder": (self._stack.push, (self._retstk.pop)),
        }

        self.funcdict[""] = (prettyprint, (self.funcdict))

    def execute(self, proglist):

        if type(proglist) not in (list, tuple):
            raise BadInternalCallException("need a tokenised list not " + repr(type(proglist)))

        self.toklist = proglist


        while True:
            global jmpd
            jmpd = False

            try:
                self.tok = self.toklist[self.idx.v]

            except IndexError:
                if len(self._stack.inspect()) > 0:
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
                    ": ignoring token '" + self.tok +
                    "' which needs a definition before it can be used"
                )
                self._stack.log(nodeftupl, 2)

            if jmpd == False:
                self.idx.v = (self.idx.v + 1, self.lit_table)

    # end def Mouse.execute

    def _lit_num(self):
        """catenate each contiguous numeral into a number, then push that"""
        import re

        num_match = re.compile(r"^([.\d]+[.\d]+|[.\d])")

        result = re.match(num_match, "".join(self.toklist[self.idx.v - 1:]))

        print(result)

        rangeof = range(self.idx.v, self.idx.v + result.span()[1])

        self.lit_table.new(self.idx.v, rangeof)

        num = result.groups()[0]
        num = float(num) if "." in num else int(num)

        self._stack.push(num)

        print("the beginning of the number was", self.idx.v, ", its end was", str(len(str(num))), ", and it looked like", str(num))

        self.idx.v = (
            self.idx.v + len(str(num)),
            self.lit_table
        )

    def _lit_string(self):
        """push everything between unescaped quotes to the stack as a list,
        then update the parser's string table with the range."""

        import re

        # get the string delimiter
        string_delim = list(self.funcdict.keys())[list(self.funcdict.values()).index((self._lit_string, ()))]

        # get the string, using the possibly custom delimiter
        expr = re.compile(
            '{}([^{}\\\\]*(?:\\\\.[^{}\\\\]*)*){}'
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

    def _lit_char(self):
        """push the charcode of the next char in the program,
        then tell the parser to skip that char"""
        try:
            self._stack.push(
                ord(self.toklist[
                            self.idx.v + 1]))
        except IndexError:
            self._stack.log("found EOF before character for literal at char " +
                str(self.char + 1) + ", line " + str(self.line) +
                " : file " + filename, 2
            )
        else:
            self.lit_table.new(self.idx.v, range(1)) # add this string to the list
            self.idx.v = (self.idx.v + 2, self.lit_table)  # skip next char


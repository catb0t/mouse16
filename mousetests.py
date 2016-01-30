#!/usr/bin/env python3

"""
testing module for mouse16.
in the case of a failed test, please file an issue to https://github.com/catb0t/mouse16
"""

import unittest
import sys
from io import StringIO
from contextlib import contextmanager


@contextmanager
def capture(command, *args, **kwargs):
    """unused capturer for stdout."""
    out, sys.stdout = sys.stdout, StringIO()
    command(*args, **kwargs)
    sys.stdout.seek(0)
    yield sys.stdout.read()
    sys.stdout = out


class CoreStack(unittest.TestCase):
    """core stack functions: direct interations with []Stack.stack"""

    def setUp(self):
        """run at the initialisation of every test"""
        stack.clean()

    def test_inspect(self):
        """stack viewer"""
        result = stack.inspect()
        self.assertEqual(result, [])
        try:
            assert result == [], \
                "fatal: failed to read the stack: not continuing"
        except AssertionError as error:
            raise RuntimeError(error) from AssertionError

    def test_inspect_fail(self):
        """no way to test this function's failure (pass)"""
        pass

    def test_push(self):
        """put something on the stack"""
        stack.push(9)
        self.assertEqual(stack.inspect(), [9])

    def test_push_fail(self):
        """no way to test this function's failure (pass)"""
        pass

    def test_pushn(self):
        """put n things on the stack"""
        stack.pushn([i for i in range(100)])
        self.assertEqual(stack.inspect(), [i for i in range(100)])

    def test_pushn_fail(self):
        """no way to test this function's failure (pass)"""
        pass

    def test_pop(self):
        """pop from stack"""
        stack.push(9)
        stack.pop()
        self.assertEqual(stack.inspect(), [])

    def test_pop_fail(self):
        """expect fail during pop"""
        with self.assertRaises(SystemExit):
            stack.pop()

    def test_popn(self):
        """pop n things from stack"""
        stack.pushn([i for i in range(1000)])
        self.assertEqual(stack.inspect(), [i for i in range(1000)])

    def test_popn_fail(self):
        """expect failure during multipop"""
        with self.assertRaises(SystemExit):
            stack.popn()

    def test_copy(self):
        """copy the top of the stack"""
        stack.push(9)
        self.assertEqual(stack.copy(), 9)

    def test_copy_fail(self):
        """expect failure during copy"""
        with self.assertRaises(SystemExit):
            stack.copy()

    def test_copyn(self):
        """copy n items from the top of the stack and return a tuple"""
        stack.pushn([i for i in range(10)])
        self.assertEqual(stack.copyn(2), stack.inspect()[-2:])

    def test_copyn_fail(self):
        """expect failure during multicopy"""
        with self.assertRaises(SystemExit):
            stack.copyn()

    def test_insert(self):
        """insert an item at an index"""
        stack.pushn([i for i in range(10)])
        stack.insert(5, 7)
        self.assertEqual(stack.inspect()[7], 5)

    def test_insert_fail(self):
        """expect failure during insertion"""
        self.assertRaises(mouse16.BadInternalCallException, stack.insert(9, 9))

    def test_insertn(self):
        """insert items at index n and up"""
        stack.pushn([i for i in range(10)])
        stack.insertn([2, 3, 4, 5], 2)
        self.assertEqual(stack.inspect()[2:6], [2, 3, 4, 5])

    def test_insertn_fail(self):
        """expect failure during multiple insertion"""
        self.assertRaises(mouse16.BadInternalCallException,
                          stack.insertn([8, 4, 12], 16))
        with self.assertRaises(TypeError):
            stack.insertn(8, 16)

    def test_remove(self):
        """remove an item from an index"""
        stack.pushn([i for i in range(10)])
        stack.remove(5)
        lst = [i for i in range(10)]
        lst.remove(5)
        self.assertEqual(stack.inspect(), lst)

    def test_remove_fail(self):
        """expect failure during by-index removal"""
        with self.assertRaises(mouse16.BadInternalCallException):
            stack.remove(1)

    def test_index(self):
        """return a 1-indexed item from the end of the list"""
        stack.pushn(list(reversed([i for i in range(10)])))
        self.assertEqual(stack.index(7), stack.inspect()[-7])

    def test_index_fail(self):
        """expect failure during index operation"""
        with self.assertRaises(IndexError):
            stack.index(16)

    def test_clean(self):
        """clear the stack and return the old stack"""
        stack.pushn([i for i in range(10)])
        self.assertNotEqual(stack.clean(), stack.inspect())


class Math(unittest.TestCase):
    """mathematical functions:
    proxied stack interactions, direct interaction with Python math operators"""

    def setUp(self):
        """run at initialisation of each test"""
        stack.clean()

    # addition

    def test_add_nums(self):
        """add numbers"""
        stack.pushn([4, 12])
        stack.add()
        self.assertEqual(stack.pop(), 16)

    def test_add_strs(self):
        """add strings"""
        stack.pushn(["cat", "dog"])
        stack.add()
        self.assertEqual(stack.pop(), "catdog")

    def test_add_numstr(self):
        """add a number to a string"""
        stack.pushn(["mouse", 16])
        stack.add()
        self.assertEqual(stack.pop(), "mouse16")

    def test_add_numstr_2(self):
        """add another number to a string"""
        stack.pushn([7, "9"])
        stack.add()
        self.assertEqual(stack.pop(), 16)

    def test_add_failure(self):
        """expect addition failure"""
        stack.pushn([{"this is a": "dictionary"}, ("this", "is", "a", "tuple")])
        self.assertRaises(mouse16.TypeWarning, stack.add())

    def test_add_failure_2(self):
        stack.pushn(["mouse", 16])
        self.assertNotEqual(stack.pop(), "mouse 16")

    # subtraction

    def test_sub_nums(self):
        """subtract numbers"""
        stack.pushn([2, 3])
        stack.sub()
        self.assertEqual(stack.pop(), -1)

    def test_sub_strs(self):
        """subtract strings"""
        stack.pushn([5, "1ll2ll3ll4ll5ll", "ll"])
        stack.sub()
        self.assertEqual(stack.pop(), "12345")

    def test_sub_numstr(self):
        """subtract a number from a string"""
        stack.pushn(["mouse16", 4])
        stack.sub()
        self.assertEqual(stack.pop(), "mou")

    def test_sub_numstr_2(self):
        stack.pushn(["20", 4])
        stack.sub()
        self.assertEqual(stack.pop(), 16)

    def test_sub_failure(self):
        """expect subtraction failure"""
        stack.pushn(["7", "asdasdasdasdasd"])
        stack.sub()
        self.assertNotEqual(stack.pop(), "asdasdas")

    # multiplication

    def test_mlt_nums(self):
        """multiply numbers"""
        stack.pushn([4, 8])
        stack.mlt()
        self.assertEqual(stack.pop(), 32)

    def test_mlt_strs(self):
        """multiply (interleave) strings"""
        stack.pushn(["cat_b0t", "mouse16"])
        stack.mlt()
        self.assertEqual(stack.pop(), "cmaotu_sbe01t6")

    def test_mlt_numstr(self):
        """multiply a string by a number"""
        stack.pushn(["mouse16", 7])
        stack.mlt()
        self.assertEqual(stack.pop(), "mouse16" * 7)

    def test_mlt_failure(self):
        """expect failure during multiply"""
        stack. pushn([("i'm a", "tuple"), "imastring"])
        self.assertRaises(mouse16.TypeWarning, stack.mlt())

    # divmod

    def test_dmd_nums(self):
        """divide numbers"""
        stack.pushn([45, 3])
        stack.dmd()
        self.assertEqual(stack.inspect(), [0, 15])

    def test_dmd_strs(self):
        """divide strings"""
        stack.pushn(["string", "alsoa_str"])
        self.assertRaises(mouse16.TypeWarning, stack.dmd())

    def test_dmd_numstr(self):
        """divide string by num or vice versa"""
        stack.pushn(["string", 123])
        self.assertRaises(mouse16.TypeWarning, stack.dmd())

    def test_dmd_failure(self):
        """expect failure during divmod"""
        stack.pushn([0, 0])
        with self.assertRaises(SystemExit):
            stack.dmd()

    def test_dmd_failure_2(self):
        """expect failure during divmod"""
        stack.pushn(["8", 0])
        self.assertRaises(mouse16.TypeWarning, stack.dmd())

    # floor div

    def test_flr_nums(self):
        """floor divide numbers"""
        stack.pushn([1, 3])
        stack.flr()
        self.assertEqual(stack.pop(), 0)

    def test_flr_strs(self):
        """floor divide strings"""
        stack.pushn(["abc", "def"])
        self.assertRaises(mouse16.TypeWarning, stack.flr())

    def test_flr_numstr(self):
        """floor divide a string with a number"""
        stack.pushn(["asd", 7])
        self.assertRaises(mouse16.TypeWarning, stack.flr())

    def test_flr_failure(self):
        """expect failure during floor division"""
        stack.pushn([0, 0])
        with self.assertRaises(SystemExit):
            stack.flr()

    # less than

    def test_lss_nums(self):
        """order numbers"""
        stack.pushn([7, 9])
        stack.lss()
        self.assertEqual(stack.pop(), 1)

    def test_lss_strs(self):
        """order strings"""
        stack.pushn(["a", "zz"])
        stack.lss()
        self.assertEqual(stack.pop(), 1)

    def test_lss_numstr(self):
        """order strings and numbers"""
        stack.pushn(["abcd", 57])
        self.assertRaises(mouse16.TypeWarning, stack.lss())

    def test_lss_failure(self):
        """expect failure ordering incoherent types"""
        stack.pushn(["asdc", ("this", "tuple")])
        self.assertRaises(mouse16.TypeWarning, stack.lss())

    # greater

    def test_gtr_nums(self):
        """order numbers"""
        stack.pushn([5, -1])
        stack.gtr()
        self.assertEqual(stack.pop(), 1)

    def test_gtr_strs(self):
        """order strings"""
        stack.pushn(["zz", "a"])
        stack.gtr()
        self.assertEqual(stack.pop(), 1)

    def test_gtr_numstr(self):
        """order strings and numbers"""
        stack.pushn(["abcd", 57])
        self.assertRaises(mouse16.TypeWarning, stack.gtr())

    def test_gtr_failure(self):
        """expect failure ordering incoherent types"""
        stack.pushn(["asdc", ("this", "tuple")])
        self.assertRaises(mouse16.TypeWarning, stack.gtr())

    # equal

    def test_equ_nums(self):
        """binary equality testing"""
        stack.pushn([16, 16])
        stack.equ()
        self.assertEqual(stack.pop(), 1)

    def test_equ_nums_neq(self):
        """binary inequality testing"""
        stack.pushn([16, 32])
        stack.equ()
        self.assertEqual(stack.pop(), 0)

    def test_equ_strs(self):
        """string equality"""
        stack.pushn(["abc", "abc"])
        stack.equ()
        self.assertEqual(stack.pop(), 1)

    def test_equ_numstr(self):
        """sum of string chars / num equality"""
        stack.pushn(["abc", 294])
        stack.equ()
        self.assertEqual(stack.pop(), 1)

    def test_equ_failure(self):
        """expect failure testing equality on undefined types"""
        stack.pushn(["abcd", ("another", "Tuple")])
        self.assertRaises(mouse16.TypeWarning, stack.equ())

    # negation

    def test_neg_nums(self):
        """negate a number"""
        stack.push(-9)
        stack.neg()
        self.assertEqual(stack.pop(), 9)

    def test_neg_strs(self):
        """negate (reverse) a string"""
        stack.push("mouse16")
        stack.neg()
        self.assertEqual(stack.pop(), "61esuom")

    def test_neg_failure(self):
        """expect failure during negation of an undefined type"""
        stack.push(["my", "list"])
        self.assertRaises(mouse16.TypeWarning, stack.neg())


class StackOps(unittest.TestCase):
    """stack operators: proxied []Stack.stack interaction through CoreStack"""

    def setUp(self):
        """run at initialisation of each test"""
        stack.clean()

    def test_dup(self):
        """push a copy of the TOS"""
        stack.push(1)
        stack.dup()
        self.assertEqual(stack.inspect(), [1, 1])

    def test_dupn(self):
        """push a copy of the nth TOS items"""
        stack.pushn([1, 2, 3, 4])
        stack.dupn(4)
        self.assertEqual(stack.inspect(), [1, 2, 3, 4] * 2)

    def test_swap(self):
        """swap the TOS"""
        stack.pushn([1, 2])
        stack.swap()
        self.assertEqual(stack.inspect(), [2, 1])
        stack.swap()
        self.assertEqual(stack.inspect(), [1, 2])

    def test_rot(self):
        """rotate up the top three items on the stack"""
        stack.pushn([0, 1, 2, 3])
        stack.rot()
        self.assertEqual(stack.inspect(), [0, 3, 1, 2])

    def test_urot(self):
        """rotate down the top three items on the stack"""
        stack.pushn([0, 1, 2, 3])
        stack.urot()
        self.assertEqual(stack.inspect(), [0, 3, 1, 2])

    def test_roll(self):
        """roll the entire stack up"""
        stack.pushn([1, 2, 3, 4])
        stack.roll()
        self.assertEqual(stack.inspect(), [2, 3, 4, 1])

    def test_rolln(self):
        """roll the entire stack up by n"""
        stack.pushn([1, 2, 3, 4, 5, 6, 7, 8, 9])
        stack.rolln(5)
        self.assertEqual(stack.inspect(), [6, 7, 8, 9, 1, 2, 3, 4, 5])

    def test_uroll(self):
        """roll the entire stack down"""
        stack.pushn([1, 2, 3, 4, 5])
        stack.uroll()
        self.assertEqual(stack.inspect(), [5, 1, 2, 3, 4])

    def test_urolln(self):
        """roll the entire stack down by n"""
        stack.pushn([1, 2, 3, 4, 5, 6, 7, 8, 9])
        stack.urolln(5)
        self.assertEqual(stack.inspect(), [5, 6, 7, 8, 9, 1, 2, 3, 4])

    def test_drop(self):
        """sliently drop an item from the stack"""
        stack.push(0)
        stack.drop()
        self.assertEqual(stack.inspect(), [])

    def test_dropn(self):
        """silently drop n items from the stack"""
        stack.pushn([1, 2, 3, 4, 5, 6, 7, 8])
        stack.dropn(8)
        self.assertEqual(stack.inspect(), [])

    def test_put(self):
        """print the top of the stack"""
        stack.push("asdasdasdasdasd")
        with capture(stack.put, (), ()) as output:
            self.assertEqual(output, "asdasdasdasdasd")

    def test_emit(self):
        """print the character at charcode on TOS"""
        stack.push(65)
        with capture(stack.emit, (), ()) as output:
            self.assertEqual(output, "A")

if __name__ == '__main__':
    try:
        import mouse16
    except ImportError:
        try:
            import mouse16hlink as mouse16
        except ImportError:
            print("stat: cannot stat 'mouse16.py': no such file or directory\n\
                module for testing not found (must be named mouse16 in the    \
                current directory) \
            ")
            exit(1)

    stack = mouse16.Stack()

    mouse = mouse16.Mouse()

    mouse16._FROMFILE = True  # make underflow & zero division raise SystemExit(4)

    unittest.main(verbosity=2)

# mouse16

### a concise concatenative stack-based programming language

## introduction

In the beginning, there was MUSYS, and MUSYS became Mouse-79, then Mouse-83, and most recently [Mouse-2002](https://mouse.davidgsimpson.com) by David G Simpson.

I think Mouse-2002 is a great language but it's a little too simplistic and... dumb to use for very many things.

So, from it, and Forth, and Factor, I have derived Mouse16 (following the naming convention).

In these docs, Mouse will refer to Mouse16.

This doc will try to explain all the aspects and features of the language in a readable format, however, in the case it differs from the Python interpreter, the interpreter is always right, and the docs are outdated.

Most of the importable module is fairly well documented, and Python is quite an easy language to read, so if in doubt, refer to the source.

**That being said, until I make a release / implement fully control structs and functions, this README will be mostly out-of-date. Thus, the comments and docstrings in the code are the docs for now.**

---

## about the language

### syntax

Mouse, like Forth, Joy and many other functional, concatenative stack-based languages, uses **reverse polish notation**, also commonly known as **postfix notation**. If you don't know what that is or how to write it, Wikipedia [has an article](https://en.wikipedia.org/wiki/Reverse_Polish_Notation), as do [the Mouse-2002 reference pages](https://missing.fixme).

Briefly, here's how we write an equation using **infix**:

```
2 + 2 == 5
```

Which would evaluate to something like `True` in Python.

In **postfix**:

```
2 2 + 5 =
```

Or, more concisely:

```
2 2+5=
```

Which will push `0` onto the stack (and, if nothing else was, print `0`) because of course, `2 + 2` is only `5` in Python.

This works by making use of the **stack**, perhaps the most important device in Forth and most stack-based languages.

Each **digit** puts its own value onto the stack. (Whitespace is required between numeric literals for them to evaluate separately unless the `-g` flag is passed to the interpreter.)

The **operators** are instructions which evaluate at some point to either a language builtin or a user-defined function, declared with `:`. They work by pushing and popping from the **stack**, for instance here the `+` operator pops two literals and tries to add them. Then, `5` is pushed and the `=` operator tests equality.

Of course, the `+` and `=` operators could be redefined at any time, to an arbitrary function definition.

Whitespace is almost never necessary, except for in numeric literals, and whitespace in string literals is preserved by the parser.

Operands that interact with the stack *always* follow their operands.

Stringy operators like `""` and `''` are a special case for obvious reasons.

#### operators

These are Mouse's predefined operators; of course, they are normal operators up for re- and un-assignment at any time.

##### basics


* `¶` this is a multiline comment. it spans until the next `¶` found *outside* a string literal.
 * There are no single line comments. If the comment glyph is found *only* at the beginning of lines in a file, then `¶` will denote a single line comment which is terminated by EOL.

* `123` and `123~0` are both numeric literals that push their value.
 * Of course, numeric glyphs can also be reassigned to do something other than push their value, however, doing this will wildly break much of the langauge.

* `"Hello, World!"` is a string literal which will be pushed to the stack as itself.
 * If nothing has been printed when execution ceases, the top of the stack will be printed.


* `'hello'` is a character literal: each unicode codepoint from the first `'` to the next will be pushed to the stack as a decimal literal.
 * if an odd number of `'` are found in the program, then `'` will only push the codepoint of the immediately following character.

* `[]` are **square braces**. they work by only executing what's inside them if the top of the stack is nonzero.

* `()` are **soft braces**; they denote a while loop.

* `{}` are **curly braces**; they work like a `quotation` in Factor and similar langauges by pushing a block of code onto the stack which will be executed in the current environment when popped.

* `🐭` is a unicode four-byte glyph at `U+1F42D MOUSE FACE`, which allows Mouse source introspection and the loading of arbitrary Python modules by the interpreter.

##### math

Control structures, types, and arbitrary and special operators will be covered more soon, but first, let's talk about math.

* `+` pops two operands from the stack and tries to add them together.
 * This works like it does in Python: concatenates strings, adds numbers.
 * If the operands are of differing type, then a specific operation will be performed, or a TypeWarning will be raised about the operator not having defined behaviour for that type.


* `-` pops two operands off the stack and tries to subtract the first from the second.
 * this operator's behaviour in a given circumstance is closely comparable to the addition operator's behaviour in the same circumstance.


* `*` pops two operands off the stack and tries to multiply them.
 * numeric multiplication works as expected, however multiplying two strings will interpolate them.


* `/`, called *divmod*, pops two operands off the stack, then pushes their quotient and the result of performing modulo divison on them.
 * this operation is *very* not defined for strings (if you try it, you will see), but insider information tells me it may have to do with string replacement, or perhaps regex.


* `< >` are two twinlike operators, greater- and less-than. they pop two operands and if one is greater or less than the other, respectively, push 0 or 1.
 * strings are orderable in the implementing language (Python) by the `sum()` of their character's charcodes. the same construct goes for Mouse.


* `=` tests equality; it works as you'd expect, pushing `1` if the operands are equal and `0` otherwise.

* `_` is the negation operator, it flips the sign of the item on the top of the stack.
 * on strings, this reverses the string.


* you may be sorely missing the exponentiation operator, which *is a builtin* but which isn't assigned to a glyph by default. use the function at index `0` of the Math library (covered later), or assign the interpreter-builtin one to a glyph using the `🐭` source-introspection operator, like: `{ "pow" 🐭 . } × :`.
 * if you're *not* boring, you could craft your own exponentiation function, perhaps like this one in Forth:

    ```
    : pow over swap 1 ?do over * loop nip ;
    ```

that's all for now :(



[stack overflow](http://stackoverflow.com) questions that helped shape this project:
---

* [Crafting impeccable unittests             ](http://stackoverflow.com/q/34701382)
* [Readable, controllable iterator indicies  ](http://stackoverflow.com/q/34734137)
* [Code style particulars                    ](http://stackoverflow.com/q/34746311)
* [Overloading the assignment operator       ](http://stackoverflow.com/q/34757038)
* [How to Pythonically log nonfatal errors   ](http://stackoverflow.com/q/26357367)
* [A more Pythonic switch statement          ](stackoverflow.com/a/3828986/4532996)
* [Indexing dictionaries by value            ](stackoverflow.com/a/11632952/4532996)
* and many more, to which I didn't contribute.

# mouse16

### a concise concatenative stack-based programming language

## introduction

In the beginning, there was MUSYS, and MUSYS became Mouse-79, then Mouse-83, and most recently [Mouse-2002](https://mouse.davidgsimpson.com) by David G Simpson.

I think Mouse-2002 is a great language but it's a little too simplistic and... dumb to use for very many things.

So, from it, and Forth, and Factor, I have derived Mouse16 (following the naming convention).

In these docs, Mouse will refer to Mouse16.

This doc will try to explain all the aspects and features of the language in a readable format, however, in the case it differs from the Python interpreter, the interpreter is always right, and the docs are outdated.

Most of the importable module is fairly well documented, and Python is quite an easy language to read, so if in doubt, refer to the source.

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

##### stack primitives

Next, the core stack operators, which are type-agnostic and reliable, and can be simply defined by their Forth-style stack effect.

Note that while all of the following are implemented in the Python interpeter, not all are designated operators, but can be accessed through source-introspection `🐭`. the case-insensitive NAME of the function is used to refer to the function internally.

* `$` - DUP - `( y x -- y x x )`

    push a copy of the TOS

  * to DROP (silently pop), use `{$}_.` `( x -- )`


* `%` - SWAP - `( y x -- x y )`

    swap the top two items on the stack

  * to ROT (up) the top three items on the stack, use `{%}_.` `( z y x w -- z w y x )`

   this pushes the SWAP function to the stack, then negates it (for SWAP, results in ROT)

  * to UROT (down) the top three items on the stack, use `{%}_$..` `( z y x w -- z x w y )`

   this pushes SWAP, then negates to get ROT, then duplicates ROT and pushes it twice.

* `@` - ROLL - `( z y x w -- z w y x )`

    rolls the stack upward

  * to UROLL, or roll downward, use `{@}_.`

   this pushes the ROLL function to the stack, then negates it (for ROLL pushes UROLL), then executes it

* `^` - OVER - `( z y x -- z y x y )`

    DUP second-to-top item to TOS

  * to NIP (drop second-to-top), use `{^}_.` `( y x -- x )`

    functions as the others.

  * to TUCK (dup TOS behind second-to-top) `( y x -- x y x )` use `{ "tuck" 🐭 . } \ : ` where `\` is the new operator.

##### other primitives


* <code>&#96;</code> (backtick) will pop from something from the stack and execute it as Mouse in the current environment.
 * for inserting arbitrary python for the interpreter to run, use the `⌨` extension operator.


* `!` dereferences the thing on the stack, i.e., prints its numeric address.
 * on the lowercase letter variables `a` - `z`, this returns that letter's zero-indexed position in the alphabet.
 * on the uppercase letter variables initialised to arrays of functions, this returns 2 to the power of the letter's zero-indexed position in the alphabet.
 * for other things, it will probably be the `id()` of the type of the item, or the item's

* `:`, if a `{}` quotation and a valid identifier are on the stack, will assign that quotation to be pushed whenever that identifier is used.
 * if preceded by a bare numeric literal and valid identifier that identifier will push that number.

```
ROFL:ROFL:LOL:ROFL:ROFL
           |
  L   /---------
 LOL===       []\
  L    \         \
        \_________\
           |    |
       \-----------/
```

This file is a short introduction to Mouse16's current state, and how to use it.
===

* Mouse uses Reverse Polish Notation for math. Numbers evaluate to themselves and floating-point numbers are annotated with a locale-independent decimal point. `123 45+!` should return `168` and `123 45.+!` should give `168.0`.

* Gotos `\` and conditionals `[ ]` are technically implemented, but it seems like they don't work, because they rely on the parser's table of literals for jumping the instruction pointer around the source, and the LiteralTable is currently defective.

* Yours truly has reached an identity crisis over whether Mouse16 should in fact be functional, or imperative like its predecessors. Functional languages are typically more straightforward to parse and evaulate, and yours truly is carefully avoiding crafting an AST.

* Things Mouse16 can do right now:

  1. Interpret itself and Python.

  2. Math.

  3. Stack operations.

  4. Strings from input and literals.

  5. Other things that work.

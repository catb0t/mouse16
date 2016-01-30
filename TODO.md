stuff that needs to be done
===========================

- [ ] control structs!

  - [x] if!

  - [ ] while!

  - [x] goto!

- [ ] data structs!

- [ ] functions / macros!


- [ ] source introspection (halfway there!)

- [ ] mouse module loading!

- [ ] a standard library!

- [ ] rewrite README to match implementation!

- [ ] multichar names!

- [ ] rewrite the logger so it's not a method of the stack, but its own class in its own file that implements python's logging

- [ ] fix weird nonsensical type interactions (math ops)! (just take a look at the unit tests for them)

---

done stuff
==========

- [x] numbers, math, stack ops!

- [x] strings & char literals!

- [x] arbitrary mouse execution! just push a (string or number) literal, then use <code>&#96;</code> to run the string in the current interpreter!
 * a mouse self-interpreter is possible with just <code>?&#96;</code>
 * note that running mouse inside mouse causes the stack to recurse another level; this is why the recursion limit is tripled

- [x] arbitrary python execution! push a string literal beginning with `!!PY!!` and the rest of it will be exec'd as python
  * this means it's possible to:
   1. run mouse inside python inside mouse inside python inside ... yeah.
   2. subclass and modify the running interpreter, while the program is running. try, for example, <code>"!!PY!!MyMouse = type('MyMouse', (object,), {'x': 'hello'}); m = MyMouse(); print(m.x)"&#96;</code>.
   3. have all the power of python embedded in mouse!
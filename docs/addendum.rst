Addendum
========

Performance
-----------

Bidict is written to be as performant as possible
without sacrificing other important goals,
such as safety, portability, and maintainability.

In general, using a bidict to maintain a bidirectional mapping
should exhibit about the same performance as
keeping two mutually-inverse one-directional mappings
in sync manually.
The test suite includes benchmarks so that bidict's performance
can be continuously measured and improved.

If you spot an opportunity to improve bidict's performance further,
please don't hesitate to
:doc:`file an issue or submit a pull request <contributors-guide>`.


``bidict`` Avoids Reference Cycles
----------------------------------

A careful reader might notice the following...

.. doctest::

   >>> fwd = bidict(one=1)
   >>> inv = fwd.inverse
   >>> inv.inverse is fwd
   True

...and worry that a :class:`~bidict.bidict` and its inverse
create a reference cycle.
If this were true,
in CPython this would mean that the memory for a :class:`~bidict.bidict`
could not be immediately reclaimed when you retained no more references to it,
but rather would have to wait for the next garbage collection to kick in
before it could be reclaimed.

However, :class:`~bidict.bidict`\s use a :class:`weakref.ref`
to store the inverse reference in one direction,
avoiding the strong reference cycle.
As a result, when you no longer retain
any references to a :class:`~bidict.bidict` you create,
you can be sure that its refcount in CPython drops to zero,
and that its memory will therefore be reclaimed immediately.

.. note::

   In PyPy this does not occur, as PyPy doesn't use reference counts.
   The memory for unreferenced objects in PyPy is only reclaimed
   when GC kicks in, which is unpredictable.


Terminology
-----------

- It's intentional that the term "inverse" is used rather than "reverse".

  Consider a collection of *(k, v)* pairs.
  Taking the reverse of the collection can only be done if it is ordered,
  and (as you'd expect) reverses the order of the pairs in the collection.
  But each original *(k, v)* pair remains in the resulting collection.

  By contrast, taking the inverse of such a collection
  neither requires the collection to be ordered
  nor guarantees any ordering in the result,
  but rather just replaces every *(k, v)* pair
  with the inverse pair *(v, k)*.

- "keys" and "values" could perhaps more properly be called
  "primary keys" and "secondary keys" (as in a database),
  or even "forward keys" and "inverse keys", respectively.
  :mod:`bidict` sticks with the terms "keys" and "values"
  for the sake of familiarity and to avoid potential confusion,
  but technically values are also keys themselves.

  Concretely, this allows :class:`~bidict.bidict`\s
  to return a set-like (*dict_keys*) object
  for :meth:`~bidict.bidict.values`,
  rather than a non-set-like *dict_values* object.


Missing ``bidict``\s in the Standard Library
--------------------------------------------

The Python standard library actually contains some examples
where :class:`~bidict.bidict`\s could be used for fun and profit
(depending on your ideas of fun and profit):

- The :mod:`logging` module
  contains a private ``_levelToName`` dict
  which maps integer levels like *10* to their string names like *DEBUG*.
  If I had a nickel for every time I wanted that exposed in a bidirectional map
  (and as a public attribute, no less),
  I bet I could afford some better turns of phrase.

- The :mod:`dis` module
  maintains a mapping from opnames to opcodes
  ``dis.opmap``
  and a separate list of opnames indexed by opcode
  ``dis.opnames``.
  These could be combined into a single bidict.

- Python 3's
  :mod:`html.entities` module
  maintains separate
  ``html.entities.name2codepoint`` and
  ``html.entities.codepoint2name`` dicts.
  These could be combined into a single bidict.


Caveats
-------

Non-Atomic Mutation
^^^^^^^^^^^^^^^^^^^

As with built-in dicts,
mutating operations on a :class:`~bidict.bidict` are not atomic.
If you need to mutate the same :class:`~bidict.bidict` from different threads,
use a
`synchronization primitive <https://docs.python.org/3/library/threading.html#lock-objects>`__
to coordinate access. [#]_

.. [#] *See also:*
       [`2 <https://twitter.com/teozaurus/status/518071391959388160>`__],
       [`3 <https://twitter.com/ph1/status/943240854419922945>`__]


Equivalent but distinct :class:`~collections.abc.Hashable`\s
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Consider the following:

.. doctest::

   >>> d = {1: int, 1.0: float}

How many items do you expect *d* to contain?
The actual result might surprise you:

.. doctest::

   >>> len(d)
   1

And similarly,

.. doctest::

   >>> {1: int, 1.0: float, 1+0j: complex, True: bool}
   {1: <class 'bool'>}
   >>> 1+0j in {True}
   True

(Note that ``1 == 1.0 == 1+0j == True``.)

This illustrates that a mapping cannot contain two items
with equivalent but distinct keys
(and likewise a set cannot contain two equivalent but distinct elements).
If an object that is being looked up in a set or mapping
is equal to a contained object,
the contained object will be found,
even if it is distinct.

With a :class:`~bidict.bidict`,
since values function as keys in the inverse mapping,
this behavior occurs in the inverse direction too,
and means that a :class:`~bidict.bidict` can end up with a different
but equivalent key from the corresponding value
in its own inverse:

.. doctest::

   >>> b = bidict({'false': 0})
   >>> b.forceput('FALSE', False)
   >>> b
   bidict({'FALSE': False})
   >>> b.inverse
   bidict({0: 'FALSE'})


*nan* as a Key
^^^^^^^^^^^^^^

In CPython, *nan* is especially tricky when used as a dictionary key:

.. doctest::

   >>> d = {float('nan'): 'nan'}
   >>> d
   {nan: 'nan'}
   >>> d[float('nan')]  # doctest: +SKIP
   Traceback (most recent call last):
       ...
   KeyError: nan
   >>> d[float('nan')] = 'not overwritten'
   >>> d  # doctest: +SKIP
   {nan: 'nan', nan: 'not overwritten'}

In other Python implementations such as PyPy,
*nan* behaves just like any other dictionary key.
But in CPython, beware of this unexpected behavior,
which applies to :class:`~bidict.bidict`\s too.
:mod:`bidict` contains no special-case logic
for dealing with *nan* as a key,
so bidict's behavior will match :class:`dict`'s
on whatever runtime you're using.

See e.g. `these docs
<https://doc.pypy.org/en/latest/cpython_differences.html>`__
for more info (search the page for "nan").


Simultaneous Assignment
^^^^^^^^^^^^^^^^^^^^^^^

:class:`~bidict.bidict`\s may behave differently
from dicts with respect to so-called "simultaneous assignment".

Consider the following:

.. doctest::

   >>> m = {'a': 'a', 'b': 'b'}
   >>> m['a'], m['b'] = m['b'], m['a']  # swap two values
   >>> m
   {'a': 'b', 'b': 'a'}

With a :class:`~bidict.bidict`,
simultaneous assignment cannot be used
to swap two values in this way:

.. doctest::

   >>> m = bidict({'a': 'a', 'b': 'b'})
   >>> m['a'], m['b'] = m['b'], m['a']
   Traceback (most recent call last):
       ...
   bidict.KeyAndValueDuplicationError: ('a', 'b')

This is because "simultaneous" assignments like the above
are `by definition <https://docs.python.org/3/reference/simple_stmts.html#assignment-statements>`__
just syntax sugar for:

.. code-block:: python

   # desugaring: m['a'], m['b'] = m['b'], m['a']
   tmp = (m['b'], m['a'])
   m['a'] = tmp[0]
   m['b'] = tmp[1]

and so the intermediate ``m['a'] = tmp[0]`` assignment
raises :class:`~bidict.KeyAndValueDuplicationError`
before the second half of the swap assignment has a chance to run.

For a working alternative, you can write:

.. doctest::

   >>> m.forceupdate({m['a']: m['b'], m['b']: m['a']})
   >>> m
   bidict({'a': 'b', 'b': 'a'})

----

For more in this vein,
check out :doc:`learning-from-bidict`.

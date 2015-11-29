Addendum
========

Missing bidicts in Stdlib!
--------------------------

The Python standard library actually contains some examples
where bidicts could be used for fun and profit
(depending on your ideas of fun and profit):

- The :mod:`logging` module
  contains a private ``_levelToName`` dict
  which maps integer levels like ``10`` to their string names like ``DEBUG``.
  If I had a nickel for every time I wanted that exposed in a bidirectional map
  (and as a public attribute, no less), 
  I bet I could afford some better turns of phrase.

- The :mod:`dis` module
  maintains a mapping from opnames to opcodes
  :attr:`dis.opmap`
  and a separate list of opnames indexed by opcode
  :attr:`dis.opnames`.
  These could be combined into a single bidict.

- Python 3's
  :mod:`html.entities` module /
  Python 2's
  :mod:`htmlentitydefs` module
  maintains separate
  :attr:`html.entities.name2codepoint` and
  :attr:`html.entities.codepoint2name` dicts.
  These could be combined into a single bidict.

More Caveats
------------

.. include:: caveat-frozenbidict-hash.doctest.rst.inc

.. include:: caveat-mutation.doctest.rst.inc

Other Verbiage, Esoterica, Navel Gazing, &c.
--------------------------------------------

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
  bidict sticks with the terms "keys" and "values"
  for the sake of familiarity and to avoid potential confusion,
  but technically values are also keys themselves.

  Concretely, this allows bidict to return a set-like (``dict_keys``) object
  for :attr:`bidict.values <bidict.BidirectionalMapping.values>` (Python 3) /
  :attr:`bidict.viewvalues <bidict.BidirectionalMapping.viewvalues>`
  (Python 2.7), rather than a non-set-like ``dict_values`` object.

- A bidict ``b`` keeps a reference to its inverse ``b.inv``.
  By extension, its inverse bidict keeps a reference to it (``b.inv.inv is b``).
  So even when you no longer have any references to ``b``,
  its refcount will not drop to zero
  because its inverse still has a reference to it.
  Python's garbage collector will detect this
  and reclaim the memory allocated for a bidict
  when you no longer have any references to it.

  **NOTE:** Prior to Python 3.4,
  ``__del__()`` methods prevented reference cycles from being garbage collected.
  No bidicts implement ``__del__()``,
  so this is only an issue if you implement ``__del__()`` in a bidict subclass.

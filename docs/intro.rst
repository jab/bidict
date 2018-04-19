Introduction
============

The :mod:`bidict` package provides a Pythonic
`bidirectional map <https://en.wikipedia.org/wiki/Bidirectional_map>`__
implementation
and related functionality to work with one-to-one mappings in Python.

bidict.bidict
-------------

:class:`bidict.bidict`
is the main bidirectional map data structure provided.
It implements the familiar API you're used to from dict:

.. code:: python

   >>> from bidict import bidict
   >>> element_by_symbol = bidict({'H': 'hydrogen'})
   >>> element_by_symbol
   bidict({'H': 'hydrogen'})
   >>> element_by_symbol['H']
   'hydrogen'

But it also maintains the inverse bidict via the
:attr:`~bidict.BidictBase.inv` attribute:

.. code:: python

   >>> element_by_symbol.inv
   bidict({'hydrogen': 'H'})
   >>> element_by_symbol.inv['hydrogen']
   'H'

Concise, efficient, Pythonic.


Why can't I just use a dict?
----------------------------

A skeptic writes:

    If I want a mapping associating *a* → *b* and *b* → *a*,
    I can just create the dict ``{a: b, b: a}``.
    Why bother using bidict?

One answer is better ergonomics
for maintaining a correct representation.
For example, consider what happens when we need
to change an existing association:

If we want to create the assocation *a* ⟷ *b*,
but might have already created the association *a* ⟷ *c*,
with the skeptic's approach
we would have to write:

.. code:: python

   >>> # To represent an existing association a ⟷ c in a single dict d:
   >>> d = {'a': 'c', 'c': 'a'}

   >>> # Here is what we'd have to do to make sure a ⟷ b gets associated
   >>> # regardless of what associations may be in d already:
   >>> newkey = 'a'
   >>> newval = 'b'
   >>> _sentinel = object()
   >>> oldval = d.pop(newkey, _sentinel)
   >>> if oldval is not _sentinel:
   ...     del d[oldval]
   >>> oldkey = d.pop(newval, _sentinel)
   >>> if oldkey is not _sentinel:
   ...     del d[oldkey]
   >>> d[newkey] = newval
   >>> d[newval] = newkey
   >>> d == {'a': 'b', 'b': 'a'}
   True


With bidict, we can instead just write:

.. code:: python

   >>> m = bidict({'a': 'c'})  # (match the previous initial setup)

   >>> # Here is all we need to make sure a ⟷ b:
   >>> m['a'] = 'b'

and voilà, bidict takes care of all the fussy details,
leaving us with just what we wanted:

.. code:: python

   >>> m
   bidict({'a': 'b'})

   >>> m.inv
   bidict({'b': 'a'})


Even more important...
++++++++++++++++++++++

Beyond this,
consider what would happen if we needed to work with
just the keys, values, or items that we have associated.

Since the single-dict approach
inserts values as keys into the same dict that it inserts keys into,
we'd never be able to tell our keys and values apart.

So iterating over the keys would also yield the values
(and vice versa),
with no way to tell which was which.

Iterating over the items
would yield twice as many as we wanted,
with a *(v, k)* item that we'd have to ignore
for each *(k, v)* item that we expect,
and no way to tell which was which.

.. code:: python

   >>> # Compare:
   >>> sorted(d.keys())    # gives both keys and values
   ['a', 'b']
   >>> sorted(d.values())  # gives both keys and values
   ['a', 'b']

   >>> # vs.
   >>> sorted(m.keys())    # just the keys
   ['a']
   >>> sorted(m.values())  # just the values
   ['b']

In short,
to model a bidirectional mapping,
we need two separate one-directional mappings,
one for the forward associations and one for the inverse,
that are kept in sync as the associations change.

This is exactly what bidict does under the hood,
abstracting it into a clean, simple, Pythonic interface.

bidict's APIs also provide power, flexibility, and safety,
making sure the one-to-one invariant is maintained
and inverse mappings are kept consistent,
while also helping make sure you don't accidentally
:ref:`shoot yourself in the foot <basic-usage:Values Must Be Unique>`.


Additional Functionality
------------------------

Besides the standard :class:`bidict.bidict` type,
the :mod:`bidict` module provides other bidirectional mapping variants:

- :class:`~bidict.frozenbidict`
- :class:`~bidict.OrderedBidict`
- :class:`~bidict.FrozenOrderedBidict`
- :func:`~bidict.namedbidict` – custom bidict type factory function

Additional functionality is covered in later sections.

But first let's proceed to :doc:`basic-usage`.

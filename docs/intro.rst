Introduction
============

The :mod:`bidict` library provides
several friendly, efficient data structures
for working with
`bidirectional mappings <https://en.wikipedia.org/wiki/Bidirectional_map>`__
in Python.

bidict.bidict
-------------

:class:`bidict.bidict`
is the main bidirectional mapping data structure provided.
It allows looking up the value associated with a key,
just like a :class:`dict`:

.. testsetup::

   from bidict import bidict

.. doctest::

   >>> element_by_symbol = bidict({'H': 'hydrogen'})
   >>> element_by_symbol['H']
   'hydrogen'

But it also allows looking up the key associated with a value,
via the special :attr:`~bidict.BidictBase.inverse` attribute:

.. doctest::

   >>> element_by_symbol.inverse['hydrogen']
   'H'

The :attr:`~bidict.BidictBase.inverse` attribute actually
references the entire inverse bidirectional mapping:

.. doctest::

   >>> element_by_symbol
   bidict({'H': 'hydrogen'})
   >>> element_by_symbol.inverse
   bidict({'hydrogen': 'H'})

...which is automatically kept in sync
as the original mapping is updated:

.. doctest::

   >>> element_by_symbol['H'] = 'hydrogène'
   >>> element_by_symbol.inverse
   bidict({'hydrogène': 'H'})

If you're used to working with :class:`dict`\s,
you'll feel right at home using :mod:`bidict`:

   >>> dir(element_by_symbol)
   [..., '__getitem__', ..., '__setitem__', ..., 'items', 'keys', ...]

Familiar, concise, Pythonic.


Why can't I just use a dict?
----------------------------

A skeptic writes:

    If I want a mapping associating *a* → *b* and *b* → *a*,
    I can just create the dict ``{a: b, b: a}``.
    Why bother using :mod:`bidict`?

One answer is better ergonomics
for maintaining a correct representation.
For example, to get the correct length,
you'd have to take the number reported by :func:`len`
and cut it in half.

But now consider what happens when we need
to store a new association,
and we try to do so naively:

.. code-block:: python

   >>> el_by_sym = {'H': 'hydrogen', 'hydrogen': 'H'}
   >>> # Later we need to associate 'H' with a different value
   >>> el_by_sym.update({'H': 'hydrogène', 'hydrogène': 'H'}  # Too naive

Here is what we're left with:

.. code-block:: python

   >>> el_by_sym
   {'H': 'hydrogène', 'hydrogène': 'H', 'hydrogen': 'H'}

Oops.

We forgot to look up whether
the key and value we wanted to set
already had any previous associations
and remove them as necessary.

In general, if we want to store the assocation *k* ⟷ *v*,
but we may have already stored the associations *k* ⟷ *V* or *K* ⟷ *v*,
a correct implementation using the single dict approach
would require code like this:

.. doctest::

   >>> d = {'k': 'V', 'V': 'k'}

   >>> def update(d, key, val):
   ...     _sentinel = object()
   ...     oldval = d.pop(key, _sentinel)
   ...     d.pop(oldval, None)
   ...     oldkey = d.pop(val, _sentinel)
   ...     d.pop(oldkey, None)
   ...     d.update({key: val, val: key})

   >>> update(d, 'k', 'v')
   >>> d == {'k': 'v', 'v': 'k'}
   True


With :mod:`bidict`, we can instead just write:

.. doctest::

   >>> b = bidict({'k': 'V'})
   >>> b['k'] = 'v'

And :mod:`bidict` takes care of all the fussy details,
leaving us with just what we wanted:

.. doctest::

   >>> b
   bidict({'k': 'v'})

   >>> b.inverse
   bidict({'v': 'k'})


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

.. doctest::

   >>> # Compare this...
   >>> sorted(d.keys())    # also gives values
   ['k', 'v']
   >>> sorted(d.values())  # also gives keys
   ['k', 'v']

   >>> # ...to this:
   >>> sorted(b.keys())    # just the keys
   ['k']
   >>> sorted(b.values())  # just the values
   ['v']

In short,
to model a bidirectional mapping,
we need two separate one-directional mappings,
one for the forward associations and one for the inverse,
that are kept in sync as the associations change.

This is exactly what :mod:`bidict` does under the hood,
abstracting it into a clean and ergonomic interface.

:mod:`bidict`'s APIs also provide power, flexibility, and safety,
making sure the one-to-one invariant is maintained
and inverse mappings are kept consistent,
while also helping make sure you don't accidentally
:ref:`shoot yourself in the foot <basic-usage:Values Must Be Unique>`.


Additional Functionality
------------------------

Besides the standard :class:`bidict.bidict` type,
the :mod:`bidict` module provides other bidirectional mapping variants:
:class:`~bidict.frozenbidict`,
:class:`~bidict.OrderedBidict`
:class:`~bidict.FrozenOrderedBidict`, and
:func:`~bidict.namedbidict`.
These and remaining functionality will be covered in later sections.

*But first, let's look at a few more details of* :doc:`basic-usage`.

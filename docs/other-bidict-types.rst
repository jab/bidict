Other ``bidict`` Types
======================

Now that we've covered
:doc:`basic-usage` with the :class:`bidict.bidict` type,
let's look at some other bidirectional mapping types.


Bidict Types Diagram
--------------------

.. image:: _static/bidict-types-diagram.png
   :target: _static/bidict-types-diagram.png
   :alt: bidict types diagram

All bidirectional mapping types that :mod:`bidict` provides
are subclasses of :class:`bidict.BidirectionalMapping`.
This abstract base class
extends :class:`collections.abc.Mapping`
by adding the
":attr:`~bidict.BidirectionalMapping.inverse`"
:obj:`~abc.abstractproperty`.

As you can see above,
:class:`bidict.bidict` is also
a :class:`collections.abc.MutableMapping`.
But :mod:`bidict` provides
immutable bidirectional mapping types as well.


:class:`~bidict.frozenbidict`
-----------------------------

:class:`~bidict.frozenbidict`
is an immutable, hashable bidirectional mapping type.

As you would expect,
attempting to mutate a
:class:`~bidict.frozenbidict`
causes an error:

.. doctest::

   >>> from bidict import frozenbidict
   >>> f = frozenbidict({'H': 'hydrogen'})
   >>> f['C'] = 'carbon'
   Traceback (most recent call last):
       ...
   TypeError: 'frozenbidict' object does not support item assignment


:class:`~bidict.frozenbidict`
also implements :class:`collections.abc.Hashable`,
so it's suitable for insertion into sets or other mappings:

.. doctest::

   >>> my_set = {f}      # not an error
   >>> my_dict = {f: 1}  # also not an error


:class:`~bidict.OrderedBidict`
------------------------------

:class:`bidict.OrderedBidict`
is a :class:`~bidict.MutableBidirectionalMapping`
that preserves the insertion order of its items,
and offers some additional ordering-related APIs
not offered by the plain bidict type.
It's like a bidirectional version of :class:`collections.OrderedDict`.

.. doctest::

   >>> from bidict import OrderedBidict
   >>> element_by_symbol = OrderedBidict({'H': 'hydrogen', 'He': 'helium', 'Li': 'lithium'})
   >>> element_by_symbol.inverse
   OrderedBidict({'hydrogen': 'H', 'helium': 'He', 'lithium': 'Li'})

   >>> first, second, third = element_by_symbol.values()
   >>> first, second, third
   ('hydrogen', 'helium', 'lithium')

   >>> # Insert an additional item and verify it now comes last:
   >>> element_by_symbol['Be'] = 'beryllium'
   >>> *_, last_item = element_by_symbol.items()
   >>> last_item
   ('Be', 'beryllium')


.. _extra-order-sensitive-apis:

Extra order-sensitive APIs
++++++++++++++++++++++++++

Additional, efficiently-implemented, order-sensitive APIs are provided as well,
following the example of :class:`~collections.OrderedDict`.

Namely,
:class:`~bidict.OrderedBidict` provides constant-time implementations of
:meth:`popitem(last: bool) <bidict.OrderedBidict.popitem>` and
:meth:`move_to_end(last: bool) <bidict.OrderedBidict.move_to_end>`,
which make ordered bidicts suitable to use for things like FIFO queues
and LRU caches.

.. doctest::

   >>> element_by_symbol.popitem(last=True)   # Remove the last item
   ('Be', 'beryllium')
   >>> element_by_symbol.popitem(last=False)  # Remove the first item
   ('H', 'hydrogen')

   >>> # Re-adding hydrogen after it's been removed moves it to the end:
   >>> element_by_symbol['H'] = 'hydrogen'
   >>> element_by_symbol
   OrderedBidict({'He': 'helium', 'Li': 'lithium', 'H': 'hydrogen'})

   >>> # But there's also a `move_to_end` method just for this purpose:
   >>> element_by_symbol.move_to_end('Li')
   >>> element_by_symbol
   OrderedBidict({'He': 'helium', 'H': 'hydrogen', 'Li': 'lithium'})

   >>> element_by_symbol.move_to_end('H', last=False)  # move to front
   >>> element_by_symbol
   OrderedBidict({'H': 'hydrogen', 'He': 'helium', 'Li': 'lithium'})


.. _eq-order-insensitive:

:meth:`~bidict.OrderedBidict`\'s ``__eq__()`` is order-insensitive
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

To ensure that ``==`` comparison for any bidict always upholds the
`transitive property of equality
<https://en.wikipedia.org/wiki/Equality_(mathematics)#Basic_properties>`__ and the
`Liskov substitution principle <https://en.wikipedia.org/wiki/Liskov_substitution_principle>`__,
equality tests between a bidict and another mapping
are always order-insensitive,
even for ordered bidicts:

.. doctest::

   >>> o1 = OrderedBidict({1: 1, 2: 2})
   >>> o2 = OrderedBidict({2: 2, 1: 1})
   >>> o1 == o2
   True

For order-sensitive equality tests, use
:meth:`~bidict.BidictBase.equals_order_sensitive`:

.. doctest::

   >>> o1.equals_order_sensitive(o2)
   False

(Note that this improves on the behavior of
``collections.OrderedDict.__eq__()``.
For more about this, see
:ref:`learning-from-bidict:Python surprises`.)


What about order-preserving dicts?
++++++++++++++++++++++++++++++++++

In CPython 3.6+ and all versions of PyPy,
:class:`dict` preserves insertion order.
Since bidicts are built on top of dicts,
can we get away with
using a plain bidict
in places where you need
an order-preserving bidirectional mapping?
(Assuming we don't need the :ref:`extra-order-sensitive-apis`.)

Let's look at some examples.

Order consistency between bidicts and their inverses
++++++++++++++++++++++++++++++++++++++++++++++++++++

Consider the following:

.. doctest::

    >>> b = bidict({1: -1, 2: -2, 3: -3})
    >>> b[2] = 'UPDATED'
    >>> b
    bidict({1: -1, 2: 'UPDATED', 3: -3})

So far so good, but look what happens to the inverse:

.. doctest::

    >>> b.inverse
    bidict({-1: 1, -3: 3, 'UPDATED': 2})

After the mutation, the ordering of the items
in the plain bidict is no longer consistent with its inverse.

To ensure that ordering is kept consistent
between a bidict and its inverse,
no matter how it's mutated,
you have to use an ordered bidict:

.. doctest::

    >>> ob = OrderedBidict({1: -1, 2: -2, 3: -3})
    >>> ob[2] = 'UPDATED'
    >>> ob
    OrderedBidict({1: -1, 2: 'UPDATED', 3: -3})
    >>> ob.inverse  # better:
    OrderedBidict({-1: 1, 'UPDATED': 2, -3: 3})


Preserving insertion order of items even after key changes
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

Another way that ordered bidicts differ from plain bidicts
is that you can change the *key* of an existing item,
and its order will still be preserved.

Let's look at an example:

.. doctest::

    >>> bi = bidict({1: -1})
    >>> ob = OrderedBidict({1: -1})
    >>> bi.forceupdate({2: -2, 3: -1})
    >>> ob.forceupdate({2: -2, 3: -1})

This update changes the key of the existing item with value -1.
In the ordered bidict, this change is performed in-place,
preserving the insertion order.
The item with value -1 was the first item inserted,
and it remains the first item even after the update:

    >>> ob
    OrderedBidict({3: -1, 2: -2})

In the plain bidict, however,
the changed item has now been moved to the end:

    >>> bi
    bidict({2: -2, 3: -1})

Note that if you insert an item that changes
the key of one existing item and the value of another existing item,
the behavior described in
:ref:`basic-usage:collapsing overwrites`
still applies.


Trade-offs
++++++++++

Like plain bidicts (and plain dicts too, for that matter),
ordered bidicts take *O(n)* space.
But to preserve insertion order,
as well as implement the :ref:`extra-order-sensitive-apis`
in constant time,
it costs :class:`~bidict.OrderedBidict`
a higher constant factor in its *O(n)* space complexity.

If you depend on preserving insertion order,
an unordered bidict may be sufficient if:

* you'll never mutate it
  (in which case, use a :class:`~bidict.frozenbidict`),
  or:

* you only mutate by removing and/or adding whole new items,
  never changing just the key or value of an existing item,
  or:

* you are okay with
  inconsistent ordering between a bidict and its inverse
  after changing the key or value of an existing item,
  as well as with items moving to the end when you change their key
  rather than being changed in place.

That said, if your code depends on the ordering,
using an :class:`~bidict.OrderedBidict` makes for clearer code,
and ensures that insertion order will be preserved
no matter what mutations you perform.

The :ref:`extra-order-sensitive-apis`
that :class:`~bidict.OrderedBidict` gives you
also expand the range of use cases
where your bidict would be suitable,
as mentioned above.


Reversing a bidict
------------------

All provided bidict types are reversible
(since they are backed by dicts,
which are themselves reversible on all supported Python versions
as of CPython 3.8+).

.. doctest::

    >>> b = bidict({1: 'one', 2: 'two', 3: 'three'})
    >>> list(reversed(b))
    [3, 2, 1]
    >>> list(reversed(b.items()))  # keys/values/items views are reversible too
    [(3, 'three'), (2, 'two'), (1, 'one')]


Polymorphism
------------

Code that needs to check only whether an object is *dict-like*
should not use ``isinstance(obj, dict)``.
This check is too specific, because dict-like objects need not
actually be instances of dict or a dict subclass.
You can see this for many dict-like objects in the standard library:

.. doctest::

   >>> from collections import ChainMap
   >>> chainmap = ChainMap()
   >>> isinstance(chainmap, dict)
   False

The same is true for all the bidict types:

.. doctest::

   >>> bi = bidict()
   >>> isinstance(bi, dict)
   False

A better way to check whether an object is dict-like
is to use the :class:`~collections.abc.Mapping`
abstract base class (ABC)
from the :mod:`collections.abc` module,
which provides a number of ABCs
intended for this purpose:

.. doctest::

   >>> isinstance(chainmap, Mapping)
   True
   >>> isinstance(bi, Mapping)
   True

Also note that the proper way to check whether an object
is a mutable mapping is to use the
:class:`~collections.abc.MutableMapping` ABC:

.. doctest::

   >>> isinstance(chainmap, MutableMapping)
   True
   >>> isinstance(bi, MutableMapping)
   True

To illustrate this,
here's an example of how you can combine the above
with bidict's own :class:`~bidict.BidirectionalMapping` ABC
to implement your own check for whether
an object is an immutable bidirectional mapping:

.. doctest::

   >>> def is_immutable_bimap(obj):
   ...     return (
   ...         isinstance(obj, BidirectionalMapping)
   ...         and not isinstance(obj, MutableMapping))

   >>> is_immutable_bimap(bidict())
   False

   >>> is_immutable_bimap(frozenbidict())
   True

For more you can do with :mod:`bidict`,
check out :doc:`extending` next.

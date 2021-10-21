Other ``bidict`` Types
======================

Now that we've covered
:doc:`basic-usage` with the :class:`bidict.bidict` type,
let's look at some other bidirectional mapping types.

.. testsetup::

   from bidict import bidict
   from collections.abc import Mapping, MutableMapping


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

As you may have noticed,
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
   TypeError: ...


:class:`~bidict.frozenbidict`
also implements :class:`collections.abc.Hashable`,
so it's suitable for insertion into sets or other mappings:

.. doctest::

   >>> my_set = {f}      # not an error
   >>> my_dict = {f: 1}  # also not an error

See the :class:`~bidict.frozenbidict`
API documentation for more information.


:class:`~bidict.OrderedBidict`
------------------------------

:class:`bidict.OrderedBidict`
is a :class:`~bidict.MutableBidirectionalMapping`
that preserves the ordering of its items,
and offers some additional ordering-related APIs
that non-ordered bidicts can't offer.
It's like a bidirectional version of :class:`collections.OrderedDict`.

.. doctest::

   >>> from bidict import OrderedBidict
   >>> element_by_symbol = OrderedBidict([
   ...     ('H', 'hydrogen'), ('He', 'helium'), ('Li', 'lithium')])

   >>> element_by_symbol.inverse
   OrderedBidict([('hydrogen', 'H'), ('helium', 'He'), ('lithium', 'Li')])

   >>> first, second, third = element_by_symbol.values()
   >>> first, second, third
   ('hydrogen', 'helium', 'lithium')

   >>> # Insert an additional item and verify it now comes last:
   >>> element_by_symbol['Be'] = 'beryllium'
   >>> last_item = list(element_by_symbol.items())[-1]
   >>> last_item
   ('Be', 'beryllium')

Additional ordering-related, mutating APIs
modeled after :class:`~collections.OrderedDict`, e.g.
:meth:`popitem(last=False) <bidict.OrderedBidict.popitem>` and
:meth:`~bidict.OrderedBidict.move_to_end`,
are provided as well:

.. doctest::

   >>> element_by_symbol.popitem(last=True)   # Remove the last item
   ('Be', 'beryllium')
   >>> element_by_symbol.popitem(last=False)  # Remove the first item
   ('H', 'hydrogen')

   >>> # Re-adding hydrogen after it's been removed moves it to the end:
   >>> element_by_symbol['H'] = 'hydrogen'
   >>> element_by_symbol
   OrderedBidict([('He', 'helium'), ('Li', 'lithium'), ('H', 'hydrogen')])

   >>> # But there's also a `move_to_end` method just for this purpose:
   >>> element_by_symbol.move_to_end('Li')
   >>> element_by_symbol
   OrderedBidict([('He', 'helium'), ('H', 'hydrogen'), ('Li', 'lithium')])

   >>> element_by_symbol.move_to_end('H', last=False)  # move to front
   >>> element_by_symbol
   OrderedBidict([('H', 'hydrogen'), ('He', 'helium'), ('Li', 'lithium')])

As with :class:`~collections.OrderedDict`,
updating an existing item preserves its position in the order:

.. doctest::

   >>> element_by_symbol['He'] = 'updated in place!'
   >>> element_by_symbol
   OrderedBidict([('H', 'hydrogen'), ('He', 'updated in place!'), ('Li', 'lithium')])


Collapsing overwrites
#####################

When setting an item in an ordered bidict
whose key duplicates that of an existing item,
and whose value duplicates that of a *different* existing item,
the existing item whose *value* is duplicated will be dropped,
and the existing item whose *key* is duplicated
will have its value overwritten in place:

.. doctest::

   >>> o = OrderedBidict([(1, 2), (3, 4), (5, 6), (7, 8)])
   >>> o.forceput(3, 8)  # item with duplicated value (7, 8) is dropped...
   >>> o  # and the item with duplicated key (3, 4) is updated in place:
   OrderedBidict([(1, 2), (3, 8), (5, 6)])
   >>> # (3, 8) took the place of (3, 4), not (7, 8)

   >>> o = OrderedBidict([(1, 2), (3, 4), (5, 6), (7, 8)])  # as before
   >>> o.forceput(5, 2)  # another example
   >>> o
   OrderedBidict([(3, 4), (5, 2), (7, 8)])
   >>> # (5, 2) took the place of (5, 6), not (1, 2)


.. _eq-order-insensitive:

:meth:`~bidict.OrderedBidict.__eq__` is order-insensitive
#########################################################

To ensure that equality of bidicts is transitive
(and to uphold the
`Liskov substitution principle <https://en.wikipedia.org/wiki/Liskov_substitution_principle>`__),
equality tests between an ordered bidict and other mappings
are always order-insensitive:

.. doctest::

   >>> b = bidict([('one', 1), ('two', 2)])
   >>> o1 = OrderedBidict([('one', 1), ('two', 2)])
   >>> o2 = OrderedBidict([('two', 2), ('one', 1)])
   >>> b == o1
   True
   >>> b == o2
   True
   >>> o1 == o2
   True

For order-sensitive equality tests, use
:meth:`~bidict.BidictBase.equals_order_sensitive`:

.. doctest::

   >>> o1.equals_order_sensitive(o2)
   False

Note that this differs from the behavior of
:class:`collections.OrderedDict`\'s ``__eq__()``,
by recommendation of Raymond Hettinger
(the author of :class:`~collections.OrderedDict`) himself.
He later said that making OrderedDict's ``__eq__()``
intransitive was a mistake.


What about order-preserving dicts?
##################################

In PyPy as well as CPython 3.6+,
:class:`dict` preserves insertion order.
Given that, can you get away with
using a non-ordered bidict
in places where you need
an order-preserving bidirectional mapping
(assuming you don't need the additional ordering-related, mutating APIs
offered by :class:`~bidict.OrderedBidict`
like :meth:`~bidict.OrderedBidict.move_to_end`)?

Consider this example:

.. doctest::

    >>> ob = OrderedBidict([(1, -1), (2, -2), (3, -3)])
    >>> b = bidict(ob)
    >>> ob[2] = b[2] = 'UPDATED'
    >>> ob
    OrderedBidict([(1, -1), (2, 'UPDATED'), (3, -3)])
    >>> b
    bidict({1: -1, 2: 'UPDATED', 3: -3})
    >>> b.inverse  # look what happens here
    bidict({-1: 1, -3: 3, 'UPDATED': 2})
    >>> ob.inverse  # need an OrderedBidict for full order preservation
    OrderedBidict([(-1, 1), ('UPDATED', 2), (-3, 3)])

When the value associated with the key ``2``
in the non-ordered bidict ``b`` was changed,
the corresponding item stays in place in the forward mapping,
but moves to the end of the inverse mapping.
Since non-ordered bidicts
provide weaker ordering guarantees
(which allows for a more efficient implementation),
it's possible to see behavior like in the example above
after certain sequences of mutations.

That said, if you depend on preserving insertion order,
a non-ordered bidict may be sufficient if:

* you'll never mutate it
  (in which case, use a :class:`~bidict.frozenbidict`),
  or:

* you only mutate by removing and/or adding whole new items,
  never changing just the key or value of an existing item,
  or:

* you're only changing existing items in the forward direction
  (i.e. changing values by key, rather than changing keys by value),
  and only depend on the order in the forward bidict,
  not the order of the items in its inverse.

On the other hand, if your code is actually depending on the order,
using an ordered bidict explicitly makes for clearer code.

:class:`~bidict.OrderedBidict` also gives you
additional ordering-related mutating APIs, such as
:meth:`~bidict.OrderedBidict.move_to_end` and
:meth:`popitem(last=False) <bidict.OrderedBidict.popitem>`,
should you ever need them.

(And on Python < 3.8,
:class:`~bidict.OrderedBidict` also gives you
:meth:`~bidict.OrderedBidict.__reversed__`.
On Python 3.8+, all bidicts are :class:`reversible <collections.abc.Reversible>`
as of :ref:`v0.21.3 <changelog>`.)


:class:`~bidict.FrozenOrderedBidict`
------------------------------------

:class:`~bidict.FrozenOrderedBidict`
is an immutable ordered bidict type.
It's like a :class:`hashable <collections.abc.Hashable>` :class:`~bidict.OrderedBidict`
without the mutating APIs,
or like a :class:`reversible <collections.abc.Reversible>`
:class:`~bidict.frozenbidict` even on Python < 3.8.
(All :class:`~bidict.bidict`\s are
`order-preserving when never mutated <What about order-preserving dicts>`__,
so :class:`~bidict.frozenbidict` is already order-preserving,
but only on Python 3.8+, where :class:`dict`\s
are :class:`reversible <collections.abc.Reversible>`,
are all :class:`~bidict.bidict`\s (including :class:`~bidict.frozenbidict`)
also :class:`reversible <collections.abc.Reversible>`.)

If you are using Python 3.8+,
:class:`~bidict.frozenbidict` gives you everything that
:class:`~bidict.FrozenOrderedBidict` gives you,
but with less space overhead.


:func:`~bidict.namedbidict`
---------------------------

:func:`bidict.namedbidict`,
inspired by :func:`collections.namedtuple`,
allows you to easily generate
a new bidirectional mapping type
with custom attribute-based access to forward and inverse mappings:

.. doctest::

   >>> from bidict import namedbidict
   >>> ElementMap = namedbidict('ElementMap', 'symbol', 'name')
   >>> noble_gases = ElementMap(He='helium')
   >>> noble_gases.name_for['He']
   'helium'
   >>> noble_gases.symbol_for['helium']
   'He'
   >>> noble_gases.name_for['Ne'] = 'neon'
   >>> del noble_gases.symbol_for['helium']
   >>> noble_gases
   ElementMap({'Ne': 'neon'})

Using the *base_type* keyword arg –
whose default value is :class:`bidict.bidict` –
you can override the bidict type used as the base class,
allowing the creation of e.g. a named frozenbidict type:

.. doctest::

   >>> ElMap = namedbidict('ElMap', 'symbol', 'name', base_type=frozenbidict)
   >>> noble = ElMap(He='helium')
   >>> noble.symbol_for['helium']
   'He'
   >>> hash(noble) is not TypeError  # does not raise TypeError: unhashable type
   True
   >>> noble['C'] = 'carbon'  # mutation fails
   Traceback (most recent call last):
   ...
   TypeError: ...


Polymorphism
------------

(Or: ABCs ftw!)

You may be tempted to write something like ``isinstance(obj, dict)``
to check whether ``obj`` is a :class:`~collections.abc.Mapping`.
However, this check is too specific, and will fail for many
types that implement the :class:`~collections.abc.Mapping` interface:

.. doctest::

   >>> from collections import ChainMap
   >>> issubclass(ChainMap, dict)
   False

The same is true for all the bidict types:

.. doctest::

   >>> issubclass(bidict, dict)
   False

The proper way to check whether an object
is a :class:`~collections.abc.Mapping`
is to use the abstract base classes (ABCs)
from the :mod:`collections` module
that are provided for this purpose:

.. doctest::

   >>> issubclass(ChainMap, Mapping)
   True
   >>> isinstance(bidict(), Mapping)
   True

Also note that the proper way to check whether an object
is an (im)mutable mapping is to use the
:class:`~collections.abc.MutableMapping` ABC:


.. doctest::

   >>> from bidict import BidirectionalMapping

   >>> def is_immutable_bimap(obj):
   ...     return (isinstance(obj, BidirectionalMapping)
   ...             and not isinstance(obj, MutableMapping))

   >>> is_immutable_bimap(bidict())
   False

   >>> is_immutable_bimap(frozenbidict())
   True

Checking for ``isinstance(obj, frozenbidict)`` is too specific
and could fail in some cases.
For example, :class:`~bidict.FrozenOrderedBidict` is an immutable mapping
but it does not subclass :class:`~bidict.frozenbidict`:

.. doctest::

   >>> from bidict import FrozenOrderedBidict
   >>> obj = FrozenOrderedBidict()
   >>> is_immutable_bimap(obj)
   True
   >>> isinstance(obj, frozenbidict)
   False

Besides the above, there are several other collections ABCs
whose interfaces are implemented by various bidict types.
Have a look through the :mod:`collections.abc` documentation
if you're interested.

For more you can do with :mod:`bidict`,
check out :doc:`extending` next.

:class:`~bidict.OrderedBidict`
------------------------------

For those times when your one-to-one mapping must also support
remembering the order in which items were inserted
(à la :class:`collections.OrderedDict`),
:class:`bidict.OrderedBidict` has got your back::

    >>> from bidict import OrderedBidict
    >>> element_by_symbol = OrderedBidict([
    ...     ('H', 'hydrogen'), ('He', 'helium'), ('Li', 'lithium')])

    >>> element_by_symbol.inv
    OrderedBidict([('hydrogen', 'H'), ('helium', 'He'), ('lithium', 'Li')])

    >>> first, second, third = element_by_symbol.values()
    >>> first, second, third
    ('hydrogen', 'helium', 'lithium')

    >>> # Insert an additional item and verify it now comes last:
    >>> element_by_symbol['Be'] = 'beryllium'
    >>> last_item = list(element_by_symbol.items())[-1]
    >>> last_item
    ('Be', 'beryllium')

The additional methods of :class:`~collections.OrderedDict` are supported too::

    >>> element_by_symbol.popitem(last=True)  # Remove the last inserted item
    ('Be', 'beryllium')
    >>> element_by_symbol.popitem(last=False) # Remove the first inserted item
    ('H', 'hydrogen')

    >>> # Re-adding hydrogen after it's been removed moves it to the last item:
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
updating an existing item preserves its position in the order::

    >>> element_by_symbol['He'] = 'updated in place!'
    >>> element_by_symbol
    OrderedBidict([('H', 'hydrogen'), ('He', 'updated in place!'), ('Li', 'lithium')])

When setting an item whose key duplicates that of an existing item
and whose value duplicates that of a *different* existing item,
the existing item whose *value* is duplicated will be dropped,
and the existing item whose *key* is duplicated
will have its value overwritten in place::

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

:meth:`~bidict.FrozenOrderedBidict.__eq__` is order-insensitive
###############################################################

To ensure that equality of bidicts is transitive
(enabling conformance to the
`Liskov substitution principle <https://en.wikipedia.org/wiki/Liskov_substitution_principle>`_),
equality tests between an ordered bidict and other
:class:`~collections.abc.Mapping`\s
are always order-insensitive::

    >>> from bidict import bidict
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
:meth:`~bidict.FrozenOrderedBidict.equals_order_sensitive`::

    >>> o1.equals_order_sensitive(o2)
    False
    >>> from collections import OrderedDict
    >>> od = OrderedDict(o2)
    >>> o1.equals_order_sensitive(od)
    False

Note that this differs from the behavior of
:class:`collections.OrderedDict`\'s ``__eq__()``,
by recommendation of Raymond Hettinger (the author) himself
(who said that making OrderedDict's ``__eq__()``
intransitive was a mistake).

:class:`~bidict.OrderedBidict` also comes in a frozen flavor.
See the :class:`~bidict.FrozenOrderedBidict`
API documentation for more information.

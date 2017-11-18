:class:`OrderedBidict <bidict.OrderedBidict>`
---------------------------------------------

For those times when your one-to-one mapping must also support
remembering the order in which items were inserted
(à la :class:`collections.OrderedDict`),
:class:`bidict.OrderedBidict` and friends have got your back::

    >>> from bidict import OrderedBidict
    >>> element_by_symbol = OrderedBidict([('H', 'hydrogen'), ('He', 'helium'), ('Li', 'lithium')])
    >>> element_by_symbol.inv
    OrderedBidict([('hydrogen', 'H'), ('helium', 'He'), ('lithium', 'Li')])
    >>> first, second, third = element_by_symbol.values()
    >>> first
    'hydrogen'
    >>> second
    'helium'
    >>> third
    'lithium'
    >>> element_by_symbol.inv['beryllium'] = 'Be'
    >>> last = next(reversed(element_by_symbol))
    >>> last
    'Be'

The additional methods of :class:`collections.OrderedDict` are supported too::

    >>> element_by_symbol.popitem(last=True)
    ('Be', 'beryllium')
    >>> element_by_symbol.popitem(last=False)
    ('H', 'hydrogen')
    >>> element_by_symbol['H'] = 'hydrogen'
    >>> element_by_symbol
    OrderedBidict([('He', 'helium'), ('Li', 'lithium'), ('H', 'hydrogen')])
    >>> element_by_symbol.move_to_end('Li')  # works on Python < 3.2 too
    >>> element_by_symbol
    OrderedBidict([('He', 'helium'), ('H', 'hydrogen'), ('Li', 'lithium')])
    >>> element_by_symbol.move_to_end('H', last=False)
    >>> element_by_symbol
    OrderedBidict([('H', 'hydrogen'), ('He', 'helium'), ('Li', 'lithium')])

As with :class:`OrderedDict <collections.OrderedDict>`,
updating an existing item preserves its position in the order,
while deleting an item and re-adding it moves it to the end::

    >>> element_by_symbol['He'] = 'HELIUM'
    >>> element_by_symbol
    OrderedBidict([('H', 'hydrogen'), ('He', 'HELIUM'), ('Li', 'lithium')])
    >>> del element_by_symbol['H']
    >>> element_by_symbol['H'] = 'hydrogen'
    >>> element_by_symbol
    OrderedBidict([('He', 'HELIUM'), ('Li', 'lithium'), ('H', 'hydrogen')])

When setting an item whose key duplicates that of an existing item
and whose value duplicates that of a different existing item,
the existing item whose value is duplicated will be dropped
and the existing item whose key is duplicated
will have its value overwritten in place::

    >>> o = OrderedBidict([(1, 2), (3, 4), (5, 6), (7, 8)])
    >>> o.forceput(3, 8)
    >>> o
    OrderedBidict([(1, 2), (3, 8), (5, 6)])
    >>> o = OrderedBidict([(1, 2), (3, 4), (5, 6), (7, 8)])
    >>> o.forceput(5, 2)
    >>> o
    OrderedBidict([(3, 4), (5, 2), (7, 8)])

Equality tests between an ordered bidict and other
:class:`Mapping <collections.abc.Mapping>` instances
behave as you might expect:
An effort is made to detect when the other mapping has a guaranteed ordering,
and the comparison is made order-sensitively or -insensitively accordingly.

    >>> from collections import OrderedDict
    >>> o1 = OrderedBidict([('one', 1), ('two', 2)])
    >>> o2 = OrderedBidict([('two', 2), ('one', 1)])
    >>> o1 == o2
    False
    >>> o1 == OrderedDict(o2)
    False
    >>> o1 == dict(o2)
    True

Since Python has no "OrderedMapping" ABC,
this detection can only infer order-sensitivity based on other signals:
The comparison will be order-sensitive iff the compared-to mapping has a
``__reversed__`` method
(and its class is not :py:class:`dict`,
since on PyPY dicts have a ``__reversed__`` method
but should nonetheless be compared order-insensitively).
If this detection is insufficient for your needs, you can override
:attr:`should_compare_order_sensitive_to
<bidict.OrderedBidictBase.should_compare_order_sensitive_to>`
to implement whatever behavior you require.

:class:`OrderedBidict <bidict.OrderedBidict>` also comes in
:class:`loose <bidict.LooseOrderedBidict>` and
:class:`frozen <bidict.FrozenOrderedBidict>`
flavors.

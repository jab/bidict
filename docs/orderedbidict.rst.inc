:class:`orderedbidict <bidict.orderedbidict>`
---------------------------------------------

For those times when your one-to-one mapping must also support
remembering the order in which items were inserted
(à la :class:`collections.OrderedDict`),
:class:`bidict.orderedbidict` and friends have got your back::

    >>> from bidict import orderedbidict
    >>> element_by_symbol = orderedbidict([('H', 'hydrogen'), ('He', 'helium'), ('Li', 'lithium')])
    >>> element_by_symbol.inv
    orderedbidict([('hydrogen', 'H'), ('helium', 'He'), ('lithium', 'Li')])
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
    orderedbidict([('He', 'helium'), ('Li', 'lithium'), ('H', 'hydrogen')])
    >>> element_by_symbol.move_to_end('Li')  # works on Python < 3.2 too
    >>> element_by_symbol
    orderedbidict([('He', 'helium'), ('H', 'hydrogen'), ('Li', 'lithium')])
    >>> element_by_symbol.move_to_end('H', last=False)
    >>> element_by_symbol
    orderedbidict([('H', 'hydrogen'), ('He', 'helium'), ('Li', 'lithium')])

As with :class:`OrderedDict <collections.OrderedDict>`,
updating an existing item preserves its position in the order,
while deleting an item and re-adding it moves it to the end::

    >>> element_by_symbol['He'] = 'HELIUM'
    >>> element_by_symbol
    orderedbidict([('H', 'hydrogen'), ('He', 'HELIUM'), ('Li', 'lithium')])
    >>> del element_by_symbol['H']
    >>> element_by_symbol['H'] = 'hydrogen'
    >>> element_by_symbol
    orderedbidict([('He', 'HELIUM'), ('Li', 'lithium'), ('H', 'hydrogen')])

When setting an item whose key duplicates that of an existing item
and whose value duplicates that of a different existing item,
the existing item whose value is duplicated will be dropped
and the existing item whose key is duplicated
will have its value overwritten in place::

    >>> o = orderedbidict([(1, 2), (3, 4), (5, 6), (7, 8)])
    >>> o.forceput(3, 8)
    >>> o
    orderedbidict([(1, 2), (3, 8), (5, 6)])
    >>> o = orderedbidict([(1, 2), (3, 4), (5, 6), (7, 8)])
    >>> o.forceput(5, 2)
    >>> o
    orderedbidict([(3, 4), (5, 2), (7, 8)])

Equality tests between two ordered bidicts are *order-sensitive*.
Equality tests between an ordered bidict and an instance of some *other*
:class:`Mapping <collections.abc.Mapping>` type
(*including even* :class:`OrderedDict <collections.OrderedDict>`)
are *order-insensitive*.

    >>> o1 = orderedbidict([('one', 1), ('two', 2)])
    >>> o2 = orderedbidict([('two', 2), ('one', 1)])
    >>> o1 == o2
    False
    >>> o1 == dict(o2)
    True
    >>> from collections import OrderedDict
    >>> o1 == OrderedDict(o2)
    True

To customize this behavior, you can override
:attr:`_should_compare_order_sensitive
<bidict.OrderedBidictBase._should_compare_order_sensitive>`
in a subclass::

    >>> class MyOrderedBidict(orderedbidict):
    ...    def _should_compare_order_sensitive(self, mapping):
    ...        # Can return False to never do order-sensitive comparison. Or
    ...        # can return isinstance(mapping, (orderedbidict, OrderedDict)).
    ...        # To make order-sensitive only if mapping is reversible:
    ...        return bool(getattr(mapping, '__reversed__', None))

    >>> m = MyOrderedBidict(o1)
    >>> m == OrderedDict(o2)  # OrderedDict is reversible -> order-sensitive
    False
    >>> m == dict(o2) if CPYTHON else m != dict(o2)  # doctest: +SKIP
    True

Note that with the custom ``_should_compare_order_sensitive`` implementation above,
*comparing with a dict would be order-sensitive in PyPy but not in CPython*,
because on PyPy dicts implement `__reversed__` (!),
whereas on CPython they do not.
Watch out for that if you ever want to do something like this,
and expect consistency between CPython and PyPy.

:class:`orderedbidict <bidict.orderedbidict>` also comes in
:class:`loose <bidict.looseorderedbidict>` and
:class:`frozen <bidict.frozenorderedbidict>`
flavors.

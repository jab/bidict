``orderedbidict``
-----------------

For those times when your one-to-one mapping must also support
remembering the order in which items were inserted
à la :class:`collections.OrderedDict`,
:class:`orderedbidict <bidict.orderedbidict>` and friends have got your back::

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
    >>> # Python 3.2+ only:
    >>> element_by_symbol.move_to_end('H', last=False)  # doctest: +SKIP
    >>> element_by_symbol  # doctest: +SKIP
    orderedbidict([('H', 'hydrogen'), ('He', 'helium'), ('Li', 'lithium')])

As with :class:`collections.OrderedDict`,
equality tests between ordered bidicts are order-sensitive.
Equality tests between ordered bidicts and order-insensitive
:class:`collections.abc.Mapping` objects
are order-insensitive.

    >>> ob1 = orderedbidict([('one', 1), ('two', 2)])
    >>> ob2 = orderedbidict([('two', 2), ('one', 1)])
    >>> ob1 == ob2
    False
    >>> from bidict import bidict
    >>> ob1 == bidict(ob2)
    True

:class:`orderedbidict <bidict.orderedbidict>` also comes in
:class:`loose <bidict.looseorderedbidict>` and
:class:`frozen <bidict.frozenorderedbidict>`
flavors.

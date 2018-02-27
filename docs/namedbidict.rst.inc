:func:`~bidict.namedbidict`
---------------------------

:func:`bidict.namedbidict`,
inspired by :func:`collections.namedtuple`,
allows you to easily generate
a new bidirectional mapping type
with custom attribute-based access to forward and inverse mappings::

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
allowing the creation of e.g. a named frozenbidict type::

    >>> from bidict import frozenbidict
    >>> ElMap = namedbidict('ElMap', 'symbol', 'name', base_type=frozenbidict)
    >>> noble = ElMap(He='helium')
    >>> noble.symbol_for['helium']
    'He'
    >>> hash(noble) is not 'an error'
    True
    >>> noble['C'] = 'carbon'  # mutation fails
    Traceback (most recent call last):
    ...
    TypeError: ...

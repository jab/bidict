namedbidict
-----------

:class:`bidict.namedbidict`,
inspired by :func:`collections.namedtuple`,
allows you to easily generate
a custom bidirectional map type
with custom attribute-based access to forward and inverse mappings::

    >>> from bidict import namedbidict
    >>> ElementMap = namedbidict('ElementMap', 'symbol', 'element')
    >>> noble_gases = ElementMap(He='helium')
    >>> noble_gases.element_for['He']
    'helium'
    >>> noble_gases.symbol_for['helium']
    'He'
    >>> noble_gases.element_for['Ne'] = 'neon'
    >>> del noble_gases.symbol_for['helium']
    >>> noble_gases
    ElementMap({'Ne': 'neon'})

The ``base_type`` keyword arg,
whose default value is :class:`bidict.bidict`,
allows overriding the bidict type used as the base class,
allowing the creation of e.g. namedfrozenbidicts::

    >>> from bidict import frozenbidict
    >>> ElMap = namedbidict('ElMap', 'sym', 'el', base_type=frozenbidict)
    >>> noble = ElMap(He='helium')
    >>> hash(noble) is not 'an exception'
    True
    >>> noble['C'] = 'carbon'  # mutation fails
    Traceback (most recent call last):
    ...
    TypeError...

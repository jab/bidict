.. _intro:

Intro
=====

The :mod:`bidict` package provides a
`bidirectional map <https://en.wikipedia.org/wiki/Bidirectional_map>`_
data structure
and related functionality to work with one-to-one mappings in Python,
Pythonically.

bidict.bidict
-------------

:class:`bidict.bidict`
is the main bidirectional map data structure provided.
It implements the dict API
and thus supports the familiar getitem (bracket) syntax.
It also supports a convenient slice syntax to express inverse mapping::

    >>> element_by_symbol = bidict(H='hydrogen')
    >>> # use standard dict getitem syntax for forward mapping:
    >>> element_by_symbol['H']
    'hydrogen'
    >>> # use slice syntax for inverse mapping:
    >>> element_by_symbol[:'hydrogen']
    'H'

You can also access a bidict's inverse
using the unary inverse operator::

    >>> symbol_by_element = ~element_by_symbol
    >>> symbol_by_element
    bidict({'hydrogen': 'H'})

Concise, efficient, Pythonic.

And if you're not a fan of the ``~``,
you can also use the ``.inv`` property to get the same thing::

    >>> element_by_symbol.inv
    bidict({'hydrogen': 'H'})
    >>> element_by_symbol.inv.inv is element_by_symbol
    True

Additional Functionality
------------------------

Besides :class:`bidict.bidict`,
the :mod:`bidict` package provides additional tools
for working with one-to-one relations:

- :class:`bidict.frozenbidict`
- :class:`bidict.namedbidict`
- :class:`bidict.collapsingbidict`
- :class:`bidict.inverted`

These will be covered in later sections.

But first let's proceed to :ref:`basic-usage`.

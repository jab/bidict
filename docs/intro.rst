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
It implements the familiar API you're used to from dict::

    >>> element_by_symbol = bidict(H='hydrogen')
    >>> element_by_symbol['H']
    'hydrogen'
    >>> element_by_symbol
    bidict({'H': 'hydrogen'})

But it also maintains the inverse mapping via the ``.inv`` property::

    >>> element_by_symbol.inv
    bidict({'hydrogen': 'H'})
    >>> element_by_symbol.inv['hydrogen']
    'H'
    >>> element_by_symbol.inv.inv is element_by_symbol
    True

Concise, efficient, Pythonic.


Is This Really Necessary?
-------------------------

A skeptic writes:

    If I want a mapping *a* <-> *b*,
    I would just create a dict *{a: b, b: a}*.
    What is the advantage of bidict
    over the simplicity of the dict approach?

Glad you asked.

For one, you don't have to manually update the mapping from *b* → *a*
every time the mapping from *a* → *b* changes.
With the skeptic's method, you have to write::

    >>> d[a] = c
    >>> d[c] = a
    >>> del d[b]

instead of just ``d[a] = c``.

More significantly,
since there's no distinction between keys and values
in the skeptic's approach,
it's less a bidirectional map
than two one-directional maps destructively merged into one.
In other words,
with this approach,
you lose information about which mappings are the forward mappings
and which are the inverse.
``d.keys()`` and ``d.values()`` would each give you
the same jumble of keys and values together
with no clean way to tease them apart,
and ``d.items()`` would be the two-times-too-big
messy combination.

In short,
to model a bidirectional map,
you need two separate one-way maps
that are kept in sync as the bidirectional map changes.
What bidict does is provide a clean abstraction over this,
so you don't have to keep them in sync manually.

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

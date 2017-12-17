.. _intro:

Introduction
============

The :mod:`bidict` package provides a Pythonic
`bidirectional map <https://en.wikipedia.org/wiki/Bidirectional_map>`_
implementation
and related functionality to work with one-to-one mappings in Python.

bidict.bidict
-------------

:class:`bidict.bidict`
is the main bidirectional map data structure provided.
It implements the familiar API you're used to from dict::

    >>> from bidict import bidict
    >>> element_by_symbol = bidict(H='hydrogen')
    >>> element_by_symbol
    bidict({'H': 'hydrogen'})
    >>> element_by_symbol['H']
    'hydrogen'

But it also maintains the inverse bidict via the
:attr:`inv <bidict.BidirectionalMapping.inv>` attribute::

    >>> element_by_symbol.inv
    bidict({'hydrogen': 'H'})
    >>> element_by_symbol.inv['hydrogen']
    'H'

Concise, efficient, Pythonic.


Why Can't I Just Use A dict?
----------------------------

A skeptic writes:

    If I want a mapping *a* ↔︎ *b*,
    I would just create a dict ``{a: b, b: a}``.
    What is the advantage of bidict
    over the simplicity of the dict approach?

Glad you asked.

For one, you don't have to manually update the mapping *b* → *a*
whenever the mapping *a* → *b* changes.
With the skeptic's method,
if *a* → *b* needs to change to *a* → *c*,
you have to write::

    >>> d[a] = c  # doctest: +SKIP
    >>> d[c] = a  # doctest: +SKIP
    >>> del d[b]  # doctest: +SKIP

With bidicit, you can instead just write::

    >>> d[a] = c  # doctest: +SKIP

and the rest is taken care of for you.

But even more important,
since the dict approach
inserts values as keys into the same one-directional map it inserts keys into,
it's not a bidirectional map so much as
the destructive merge of two one-directional maps into one.

In other words,
you lose information about which mappings are the forward mappings
and which are the inverse.
``d.keys()`` and ``d.values()`` would each give you
the same 2x-too-big jumble of keys and values
all mixed together,
and ``d.items()`` would likewise be
the 2x-too-big combination of forward and inverse mappings
all mixed together.

In short,
to model a bidirectional map,
you need two separate one-directional maps
that are kept in sync as the bidirectional map changes.
This is exactly what bidict does under the hood,
abstracting this into a clean and simple interface.
bidict also provides rich and powerful facilities
to help you handle the enforcement of the one-to-one constraint
(for example, when attempting to set a new key to an existing value)
exactly as you intend.

Additional Functionality
------------------------

Besides the standard :class:`bidict.bidict` class,
the :mod:`bidict` package provides other bidict variants,
as well as additional tools
for working with one-to-one relations:

- :class:`bidict.BidirectionalMapping`
- :func:`bidict.namedbidict`
- :class:`bidict.frozenbidict`
- :class:`bidict.OrderedBidict`
- :class:`bidict.FrozenOrderedBidict`
- :class:`bidict.inverted`
- :class:`bidict.pairs`

These and other provided functionality are covered in later sections.

But first let's proceed to :ref:`basic-usage`.

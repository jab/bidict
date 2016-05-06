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
    >>> element_by_symbol.inv.inv is element_by_symbol
    True

Concise, efficient, Pythonic.


Why Can't I Just Use A dict?
----------------------------

A skeptic writes:

    If I want a mapping *a* ↔︎ *b*,
    I would just create a dict *{a: b, b: a}*.
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
*d.keys()* and *d.values()* would each give you
the same 2x-too-big jumble of keys and values
all mixed together,
and *d.items()* would likewise be
the 2x-too-big combination of forward and inverse mappings
all mixed together.

In short,
to model a bidirectional map,
you need two separate one-directional maps
that are kept in sync as the bidirectional map changes.
This is exactly what bidict does under the hood,
abstracting this into a clean and simple interface,
while providing complementary functionality to boot.

Additional Functionality
------------------------

Besides :class:`bidict.bidict`,
the :mod:`bidict` package provides additional tools
for working with one-to-one relations:

- :class:`bidict.frozenbidict`
- :class:`bidict.loosebidict`
- :class:`bidict.orderedbidict`
- :class:`bidict.frozenorderedbidict`
- :class:`bidict.looseorderedbidict`
- :class:`bidict.namedbidict`
- :class:`bidict.inverted`

These will be covered in later sections.

But first let's proceed to :ref:`basic-usage`.

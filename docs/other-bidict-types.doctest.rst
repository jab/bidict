.. _other-bidict-types:

Other bidict Types
==================

Now that we've covered
:class:`bidict.bidict`,
:class:`bidict.loosebidict`,
and some other basics,
let's look at the remaining bidict types
and the hierarchy they belong to.

bidict Class Hierarchy
----------------------

.. image:: _static/class-hierarchy.svg
    :alt: bidict class hierarchy

At the top of the bidict type hierarchy is
:class:`bidict.BidirectionalMapping`.
This implements the :class:`collections.abc.Mapping` ABC
and contains the shared logic allowing keys to be looked up by value
(as well as values to be looked up by key).
Most users will only ever need to use one of its subclasses.

At this point the type hierarchy tree forks into
a mutable branch and an immutable branch.
On the mutable side we have
:class:`bidict.bidict`
(which implements :class:`collections.abc.MutableMapping`)
and finally
:class:`bidict.loosebidict`,
the leaf on this side of the tree.

Polymorphism
++++++++++++

Note that none of the bidict types inherit from dict.
The following example demonstrates a recommended way to verify
that a bidict is dict-like::

    >>> from collections import Mapping
    >>> from bidict import bidict
    >>> b = bidict()
    >>> isinstance(b, Mapping)
    True

.. include:: frozenbidict.doctest.rst.inc

.. include:: namedbidict.doctest.rst.inc

There's one last useful bit of functionality to mention:
:ref:`the "inverted" iterator <inverted>`.

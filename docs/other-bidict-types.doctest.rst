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

Note that none of the bidict types inherit from dict::

    >>> from bidict import bidict, frozenbidict
    >>> isinstance(bidict(), dict)
    False
    >>> isinstance(frozenbidict(), dict)
    False

If you must use ``isinstance`` to check whether a bidict is dict-like,
you can use the abstract base classes from the ``collections`` module,
which is a better way to check for interface conformance::

    >>> from collections import Mapping, MutableMapping
    >>> isinstance(bidict(), MutableMapping)
    True
    >>> isinstance(frozenbidict(), Mapping)
    True

Though sometimes you can write more polymorphic code
by using duck typing rather than ``isinstance``::

    >>> mystery = object()
    >>> try:
    ...     mystery[0] = 1
    ... except TypeError:
    ...     pass
    >>> mystery2 = object()
    >>> if hasattr(mystery2, '__setitem__'):
    ...     mystery2[0] = 1

.. include:: frozenbidict.doctest.rst.inc

.. include:: namedbidict.doctest.rst.inc

There's one more bit of functionality to cover,
:ref:`the "inverted" iterator <inverted>`.

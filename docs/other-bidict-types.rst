.. _other-bidict-types:

Other bidict Types
==================

Now that we've covered
:class:`bidict.bidict`,
:class:`bidict.collapsingbidict`,
and a few :ref:`caveats`,
let's look at the remaining bidict types
and the type hierarchy they belong to.

bidict Type Hierarchy
---------------------

.. image:: _static/bidict_types.png
    :alt: bidict type hierarchy

At the top of the bidict type hierarchy is
:class:`bidict.BidirectionalMapping`.
This implements the :class:`collections.abc.Mapping` ABC
to add the logic that allows keys to be looked up by value.
Most users will only ever need to use one of its subclasses.

At this point the bidict type hierarchy branches into
mutable bidict types and immutable bidict types.
As you may have guessed,
:class:`bidict.bidict` extends BidirectionalMapping,
and since BidirectionalMapping itself only extends the the Mapping ABC,
:class:`bidict.bidict` also implements
:class:`collections.abc.MutableMapping`
making it mutable.

The leaf in this branch of the tree is :class:`bidict.collapsingbidict`
which extends :class:`bidict.bidict`.

.. include:: frozenbidict.rst.inc

.. include:: namedbidict.rst.inc

There's one last useful bit of functionality to mention:
:ref:`the "inverted" iterator <inverted>`.

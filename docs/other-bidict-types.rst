.. _other-bidict-types:

Other ``bidict`` Types
======================

Now that we've covered
:ref:`basic usage of bidict.bidict <basic-usage>` and
:ref:`bidict.loosebidict <loosebidict>`,
let's look at the remaining bidict types
and the hierarchy they belong to.

``bidict`` Type Hierarchy
-------------------------

.. image:: _static/type-hierarchy.png
    :alt: bidict type hierarchy

At the top of the hierarchy of types that bidict provides is
:class:`bidict.BidirectionalMapping`.
This extends the :class:`collections.abc.Mapping` ABC
with the
:attr:`"inv" <bidict.BidirectionalMapping.inv>`
:func:`abstractproperty <abc.abstractproperty>`,
as well as a concrete, generic implementation of
:attr:`__inverted__ <bidict.BidirectionalMapping.__inverted__>`.
:class:`BidirectionalMapping <bidict.BidirectionalMapping>` also implements
:attr:`__subclasshook__ <bidict.BidirectionalMapping.__subclasshook__>`,
so that any class providing a conforming API is considered a virtual subclass
of :class:`BidirectionalMapping <bidict.BidirectionalMapping>` automatically.

Implementing
:class:`BidirectionalMapping <bidict.BidirectionalMapping>` is
:class:`BidictBase <bidict.BidictBase>`.
Users will typically only interact with subclasses of this class.

Inheriting from :class:`BidictBase <bidict.BidictBase>`
are the already-discussed
:class:`bidict.bidict` and :class:`bidict.loosebidict`,
which implement :class:`collections.abc.MutableMapping`.

Also inheriting from :class:`BidictBase <bidict.BidictBase>`
is :class:`bidict.frozenbidict`,
the first immutable bidict you'll meet.

.. include:: frozenbidict.rst.inc

.. include:: orderedbidict.rst.inc

.. include:: namedbidict.rst.inc

.. include:: polymorphism.rst.inc

.. include:: extending.rst.inc

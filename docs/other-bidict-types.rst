.. _other-bidict-types:

Other ``bidict`` Types
======================

Now that we've covered
:doc:`basic-usage`,
let's look at the remaining bidict types
and the hierarchy they belong to.

.. _bidict-type-hierarchy:

``bidict`` Type Hierarchy
-------------------------

.. image:: _static/type-hierarchy.png
    :alt: bidict type hierarchy

At the top of the hierarchy of types that bidict provides is
:class:`bidict.BidirectionalMapping`.
This extends the :class:`collections.abc.Mapping` ABC
with the
:attr:`~bidict.BidirectionalMapping.inv`
:func:`~abc.abstractproperty`,
as well as a concrete, generic implementation of
:attr:`~bidict.BidirectionalMapping.__inverted__`.
:class:`~bidict.BidirectionalMapping` also implements
:attr:`~bidict.BidirectionalMapping.__subclasshook__`,
so that any class providing a conforming API is considered a virtual subclass
of :class:`~bidict.BidirectionalMapping` automatically.

Implementing
:class:`~bidict.BidirectionalMapping` is
:class:`~bidict.frozenbidict`,
which provides a hashable, immutable bidict type,
and serves as a base class for mutable bidict types to extend.

.. include:: frozenbidict.rst.inc

.. include:: orderedbidict.rst.inc

.. include:: namedbidict.rst.inc

.. include:: polymorphism.rst.inc

.. include:: extending.rst.inc

Proceed to :ref:`other-functionality`.

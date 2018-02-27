.. _other-bidict-types:

Other ``bidict`` Types
======================

Now that we've covered
:doc:`basic-usage`,
let's look at the remaining bidict types.

.. _bidict-types-diagram:

``bidict`` Types Diagram
------------------------

.. image:: _static/bidict-types-diagram.png
    :alt: bidict types diagram

The most abstract type that bidict provides is
:class:`bidict.BidirectionalMapping`.
This extends the :class:`collections.abc.Mapping` ABC
by adding the
":attr:`~bidict.BidirectionalMapping.inv`"
:obj:`~abc.abstractproperty`.
It also implements
:meth:`~bidict.BidirectionalMapping.__subclasshook__`,
so that any class providing a conforming API is considered a virtual subclass
of :class:`~bidict.BidirectionalMapping` automatically,
without needing to subclass :class:`~bidict.BidirectionalMapping` explicitly.

.. include:: frozenbidict.rst.inc

.. include:: orderedbidict.rst.inc

.. include:: namedbidict.rst.inc

.. include:: polymorphism.rst.inc

.. include:: extending.rst.inc

Next proceed to :ref:`other-functionality`.

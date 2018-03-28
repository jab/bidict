.. _other-bidict-types:

Other ``bidict`` Types
======================

Now that we've covered
:doc:`basic-usage` with the :class:`bidict.bidict` type,
let's look at some other bidirectional mapping types.

.. _bidict-types-diagram:

``bidict`` Types Diagram
------------------------

.. image:: _static/bidict-types-diagram.png
    :alt: bidict types diagram

All bidirectional mapping types that :mod:`bidict` provides
are subclasses of :class:`bidict.BidirectionalMapping`.
This abstract base class
extends :class:`collections.abc.Mapping`
by adding the
":attr:`~bidict.BidirectionalMapping.inv`"
:obj:`~abc.abstractproperty`. [#fn-subclasshook]_

.. [#fn-subclasshook]
    (In fact, any :class:`collections.abc.Mapping`
    that provides an ``inv`` attribute
    will be considered a virtual subclass of
    :class:`bidict.BidirectionalMapping`
    :meth:`automatically <bidict.BidirectionalMapping.__subclasshook__>`,
    enabling interoperability with external implementations.)

As you may have noticed,
:class:`bidict.bidict` is also
a :class:`collections.abc.MutableMapping`.
But :mod:`bidict` provides
immutable bidirectional mapping types as well.

.. include:: frozenbidict.rst.inc

.. include:: orderedbidict.rst.inc


:class:`~bidict.FrozenOrderedBidict`
------------------------------------

:class:`~bidict.FrozenOrderedBidict`
is an immutable ordered bidict type.
It's like an :class:`~bidict.OrderedBidict`
without the mutating APIs,
or equivalently like an order-preserving
:class:`~bidict.frozenbidict`.

.. include:: namedbidict.rst.inc

.. include:: polymorphism.rst.inc

.. include:: extending.rst.inc

Next proceed to :ref:`other-functionality`.

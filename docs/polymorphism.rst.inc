.. _polymorphism:

Polymorphism
------------

a.k.a "Know your ABCs"

You may be tempted to write something like ``isinstance(obj, dict)``
to check whether ``obj`` is a :class:`~collections.abc.Mapping`.
However, this check is too specific, and will fail for many
types that implement the :class:`~collections.abc.Mapping` interface::

    >>> from collections import ChainMap  # (Python 3+) # doctest: +SKIP
    >>> issubclass(ChainMap, dict)  # doctest: +SKIP
    False

The same is true for all the bidict types::

    >>> from bidict import bidict
    >>> issubclass(bidict, dict)
    False

The proper way to check whether an object
is a :class:`~collections.abc.Mapping`
is to use the abstract base classes (ABCs)
from the :mod:`collections` module
that are provided for this purpose::

    >>> from collections import Mapping  # doctest: +SKIP
    >>> issubclass(ChainMap, Mapping)  # doctest: +SKIP
    True
    >>> isinstance(bidict(), Mapping)  # doctest: +SKIP
    True

Also note that the proper way to check whether an object
is an (im)mutable mapping is to use the
:class:`~collections.abc.MutableMapping` ABC::

    >>> from collections import MutableMapping
    >>> from bidict import BidirectionalMapping, frozenbidict

    >>> def is_immutable_bimap(obj):
    ...     return (isinstance(obj, BidirectionalMapping)
    ...             and not isinstance(obj, MutableMapping))

    >>> is_immutable_bimap(bidict())
    False

    >>> is_immutable_bimap(frozenbidict())
    True

Checking for ``isinstance(obj, frozenbidict)`` is too specific
and could fail in some cases.
For example, :class:`~bidict.FrozenOrderedBidict` is an immutable mapping
but it does not subclass :class:`~bidict.frozenbidict`::

    >>> from bidict import FrozenOrderedBidict
    >>> obj = FrozenOrderedBidict()
    >>> is_immutable_bimap(obj)
    True
    >>> isinstance(obj, frozenbidict)
    False

Besides the above, there are several other collections ABCs
whose interfaces are implemented by various bidict types.
Have a look through the :mod:`collections.abc` documentation
if you're interested.

One thing you might notice is that there is no
``Ordered`` or ``OrderedMapping`` ABC.
However, Python 3.6 introduced the :class:`collections.abc.Reversible` ABC.
Since being reversible implies having an ordering,
you could check for reversibility instead.
For example::

    >>> from collections import Reversible  # doctest: +SKIP
    >>> def is_reversible_mapping(cls):
    ...     return issubclass(cls, Reversible) and issubclass(cls, Mapping)
    ...

    >>> from bidict import OrderedBidict
    >>> is_reversible_mapping(OrderedBidict)  # doctest: +SKIP
    True

    >>> from collections import OrderedDict
    >>> is_ordered_mapping(OrderedDict)  # doctest: +SKIP
    True

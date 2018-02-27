.. _polymorphism:

Polymorphism
------------

a.k.a "Know your ABCs"

You may be tempted to write something like ``isinstance(obj, dict)``
to check whether ``obj`` is a :class:`~collections.abc.Mapping`.
However, this check is too specific, and will fail for many
types that implement the :class:`~collections.abc.Mapping` interface::

    >>> try:
    ...     from collections import ChainMap
    ... except ImportError:  # not available in Python 2
    ...     ChainMap = None  # Could try with a Python 2 ChainMap shim if in doubt.
    >>> issubclass(ChainMap, dict) if ChainMap else False
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

    >>> from collections import Mapping
    >>> issubclass(ChainMap, Mapping) if ChainMap else True
    True
    >>> isinstance(bidict(), Mapping)
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
Namely, :class:`~bidict.FrozenOrderedBidict` is an immutable mapping
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
if you need to check for an ordered mapping,
you could check for reversibility instead.
For example::

    >>> def is_reversible(cls):
    ...     try:
    ...         from collections import Reversible
    ...     except ImportError:  # Python < 3.6
    ...         # Better to use a shim of Python 3.6's Reversible,
    ...         # but this'll do for now:
    ...         return getattr(cls, '__reversed__', None) is not None
    ...     return issubclass(cls, Reversible)

    >>> def is_ordered_mapping(cls):
    ...     return is_reversible(cls) and issubclass(cls, Mapping)
    ...

    >>> from bidict import OrderedBidict
    >>> is_ordered_mapping(OrderedBidict)
    True

    >>> from collections import OrderedDict
    >>> is_ordered_mapping(OrderedDict)
    True

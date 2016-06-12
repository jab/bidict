.. _polymorphism:

Polymorphism
------------

Note that none of the bidict types inherit from dict::

    >>> from bidict import bidict, frozenbidict
    >>> isinstance(bidict(), dict)
    False
    >>> isinstance(frozenbidict(), dict)
    False

If you must use :func:`isinstance` to check whether a bidict is dict-like,
you can use the abstract base classes from the :mod:`collections` module,
which is a better way to check for interface conformance::

    >>> from collections import Mapping, MutableMapping
    >>> isinstance(bidict(), MutableMapping)
    True
    >>> isinstance(frozenbidict(), Mapping)
    True

Though you can often write more polymorphic code
by using duck typing rather than :func:`isinstance`::

    >>> mystery = object()
    >>> try:
    ...     mystery[0] = 1
    ... except TypeError:
    ...     pass
    >>> mystery2 = object()
    >>> if hasattr(mystery2, '__setitem__'):
    ...     mystery2[0] = 1

.. _polymorphism:

Polymorphism
------------

Note that none of the bidict types inherit from dict::

    >>> from bidict import bidict
    >>> isinstance(bidict(), dict)
    False

If you must use :func:`isinstance` to check whether a bidict is dict-like,
you can use the abstract base classes from the :mod:`collections` module,
which is a better way to check for interface conformance::

    >>> from collections import Mapping, MutableMapping
    >>> isinstance(bidict(), Mapping)
    True
    >>> isinstance(bidict(), MutableMapping)
    True

Though you can often write more polymorphic code
by using duck typing rather than :func:`isinstance`::

    >>> # LBYL-style:
    >>> if hasattr(foo, '__setitem__'):  # doctest: +SKIP
    ...     foo[0] = 1
    >>> # EAFP-style:
    >>> try:  # doctest: +SKIP
    ...     bar[0] = 1
    ... except TypeError:
    ...     # plan B

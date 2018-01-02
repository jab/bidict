.. _polymorphism:

Polymorphism
------------

Note that none of the bidict types inherit from dict::

    >>> from bidict import bidict
    >>> isinstance(bidict(), dict)
    False

If you must use :func:`isinstance` to check whether a bidict is dict-like,
you can use the abstract base classes from the :mod:`collections` module,
which is the proper way to check if an object is a mapping::

    >>> from collections import Mapping, MutableMapping
    >>> isinstance(bidict(), Mapping)
    True
    >>> isinstance(bidict(), MutableMapping)
    True

Of course you can also use duck typing to avoid :func:`isinstance` altogether::

    >>> # EAFP-style:
    >>> try:  # doctest: +SKIP
    ...     foo['bar'] = 'baz'
    ... except TypeError:
    ...     # plan B

    >>> # LBYL-style:
    >>> if hasattr(foo, '__setitem__'):  # doctest: +SKIP
    ...     foo['bar'] = 'baz'

Also note that since
:class:`~bidict.bidict` extends
:class:`~bidict.frozenbidict`,
if you need to check whether a bidict is immutable,
testing for ``isinstance(foo, frozenbidict)``
is not what you want::

    >>> from bidict import frozenbidict
    >>> isinstance(bidict(), frozenbidict)
    True

Instead you can check for
``isinstance(foo, Hashable)`` or
``isinstance(foo, MutableMapping)`` to get the desired behavior::

    >>> from collections import Hashable
    >>> isinstance(frozenbidict(), Hashable)
    True
    >>> isinstance(bidict(), Hashable)
    False
    >>> isinstance(bidict(), MutableMapping)
    True
    >>> isinstance(frozenbidict(), MutableMapping)
    False

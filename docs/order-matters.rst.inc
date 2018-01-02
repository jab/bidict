Order Matters
+++++++++++++

Performing a bulk insert operation
(e.g. on initialization or
via :func:`~bidict.bidict.update`,
:func:`~bidict.bidict.forceupdate`,
or :func:`~bidict.bidict.putall`),
is like performing a sequence of single insert operations
for each of the provided items
(with the advantage that the bulk insert fails clean, i.e. if it fails,
it will be as if none of the single insert operations were ever called).
Therefore, the order of the items provided to the bulk insert operation
may affect the result::

    >>> from bidict import bidict
    >>> b = bidict({0: 0, 1: 2})
    >>> b.forceupdate([(2, 0), (0, 1), (0, 0)])
    >>> # 1. (2, 0) overwrites (0, 0)             -> bidict({2: 0, 1: 2})
    >>> # 2. (0, 1) is added                      -> bidict({2: 0, 1: 2, 0: 1})
    >>> # 3. (0, 0) overwrites (0, 1) and (2, 0)  -> bidict({0: 0, 1: 2})
    >>> sorted(b.items())
    [(0, 0), (1, 2)]
    >>> b = bidict({0: 0, 1: 2})  # as before
    >>> # Give same items to forceupdate() but in a different order:
    >>> b.forceupdate([(0, 1), (0, 0), (2, 0)])
    >>> # 1. (0, 1) overwrites (0, 0)             -> bidict({0: 1, 1: 2})
    >>> # 2. (0, 0) overwrites (0, 1)             -> bidict({0: 0, 1: 2})
    >>> # 3. (2, 0) overwrites (0, 0)             -> bidict({1: 2, 2: 0})
    >>> sorted(b.items())  # different result
    [(1, 2), (2, 0)]

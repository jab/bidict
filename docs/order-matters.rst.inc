Order Matters
+++++++++++++

Performing a bulk insert operation –
i.e. passing multiple items to
:meth:`~bidict.BidictBase.__init__`,
:func:`~bidict.bidict.update`,
:func:`~bidict.bidict.forceupdate`,
or :func:`~bidict.bidict.putall` –
is like inserting each of those items individually in sequence.
[#fn-fail-clean]_

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
    >>> # Give the same items to forceupdate() but in a different order:
    >>> b.forceupdate([(0, 1), (0, 0), (2, 0)])

    >>> # 1. (0, 1) overwrites (0, 0)             -> bidict({0: 1, 1: 2})
    >>> # 2. (0, 0) overwrites (0, 1)             -> bidict({0: 0, 1: 2})
    >>> # 3. (2, 0) overwrites (0, 0)             -> bidict({1: 2, 2: 0})

    >>> sorted(b.items())  # different items!
    [(1, 2), (2, 0)]


.. [#fn-fail-clean]

    Albeit with an extremely important advantage:
    bulk insertion *fails clean*.
    i.e. If a bulk insertion fails,
    it will leave the bidict in the same state it was before,
    with none of the provided items inserted.

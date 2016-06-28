Other Functionality
===================

``inverted()``
--------------

bidict provides the :class:`inverted() <bidict.inverted>` iterator
to help you get inverse pairs from various types of objects.

Pass in a mapping to get the inverse mapping::

    >>> from bidict import inverted
    >>> it = inverted({1: 'one'})
    >>> {k: v for (k, v) in it}
    {'one': 1}

...an iterable of pairs to get the pairs' inverses::

    >>> list(inverted([(1, 'one'), (2, 'two')]))
    [('one', 1), ('two', 2)]
    >>> list(inverted((i*i, i) for i in range(2, 5)))
    [(2, 4), (3, 9), (4, 16)]

...or any object implementing an ``__inverted__`` method,
which objects that already know their own inverses (such as bidicts)
can implement themselves::

    >>> from bidict import bidict, orderedbidict
    >>> dict(inverted(bidict({1: 'one'})))
    {'one': 1}
    >>> list(inverted(orderedbidict([(2, 4), (3, 9)])))
    [(4, 2), (9, 3)]


Extras
------

:func:`bidict.pairs`
as well as the :mod:`bidict.compat` module
are used internally,
but are exported as well
since they may also be of use externally.

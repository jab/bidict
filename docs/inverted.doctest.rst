.. _inverted:

inverted 
========

The :class:`bidict.inverted` iterator
(inspired by the :func:`reversed` built-in)
is provided to help with getting the inverse
of any kind of object that can be inverted.

Pass in a mapping to get the inverse mapping::

    >>> from bidict import bidict, inverted
    >>> dict(inverted({1: 'one'}))
    {'one': 1}

an iterable of pairs to get the pairs' inverses::

    >>> list(inverted([(1, 'one'), (2, 'two')]))
    [('one', 1), ('two', 2)]
    >>> list(inverted((i*i, i) for i in range(2, 5)))
    [(2, 4), (3, 9), (4, 16)]

or any object implementing an ``__inverted__`` method::

    >>> dict(inverted(bidict({1: 'one'})))
    {'one': 1}

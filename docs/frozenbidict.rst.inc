frozenbidict
------------

Having BidirectionalMapping extend the Mapping ABC rather than MutableMapping
allows for an *immutable* bidict type to extend from *it*.
This type is called :class:`bidict.frozenbidict`
(by analogy to :class:`frozenset`),
and provides the other branch of the bidict type tree.

As you would expect,
attempting to mutate a frozenbidict after initializing it causes an error::

    >>> f = frozenbidict()
    >>> f['C'] = 'carbon'
    Traceback (most recent call last):
    ...
    TypeError...

Besides extending BidirectionalMapping,
frozenbidict implements :class:`collections.abc.Hashable`.
Thus it's suitable for insertion into sets or other maps::

    >>> f = frozenbidict()
    >>> set([f]) is not 'an error'
    True

as expected of an immutable type.

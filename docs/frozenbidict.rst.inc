``frozenbidict``
----------------

Having :class:`bidict.BidirectionalMapping`
extend the Mapping ABC rather than MutableMapping
allows for an *immutable* bidict type to extend from *it*.
This type is called :class:`bidict.frozenbidict`,
and makes up the other branch of the tree.

As you would expect,
attempting to mutate a frozenbidict after initializing it causes an error::

    >>> from bidict import frozenbidict
    >>> f = frozenbidict()
    >>> f['C'] = 'carbon'
    Traceback (most recent call last):
        ...
    TypeError...

Besides extending :class:`BidirectionalMapping <bidict.BidirectionalMapping>`,
frozenbidict implements :class:`collections.abc.Hashable`.
Thus it's suitable for insertion into sets or other maps::

    >>> f = frozenbidict()
    >>> set([f]) is not 'an error'
    True

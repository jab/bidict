:class:`frozenbidict <bidict.frozenbidict>`
-------------------------------------------

Having :class:`bidict.BidirectionalMapping`
extend :class:`collections.abc.Mapping`
rather than :class:`MutableMapping <collections.abc.MutableMapping>`
allows for an *immutable* bidict type to extend from *it*.
This type is called :class:`bidict.frozenbidict`,
and makes up the other branch of the tree.

As you would expect,
attempting to mutate a frozenbidict after initializing it causes an error::

    >>> from bidict import frozenbidict
    >>> f = frozenbidict({'H': 'hydrogen'})
    >>> f['C'] = 'carbon'
    Traceback (most recent call last):
        ...
    TypeError...

Because it is immutable, :class:`frozenbidict <bidict.frozenbidict>`
implements :class:`collections.abc.Hashable`.
Thus it's suitable for insertion into sets or other mappings::

    >>> {f} is not 'an error'
    True
    >>> {f: 1} is not 'an error'
    True

See the :class:`bidict.frozenbidict` and :class:`bidict.frozenorderedbidict`
API documentation for more information on implementation details if necessary.

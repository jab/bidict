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

Besides extending :class:`BidirectionalMapping <bidict.BidirectionalMapping>`,
frozenbidict implements :class:`collections.abc.Hashable`.
Thus it's suitable for insertion into sets or other mappings::

    >>> set([f]) is not 'an error'
    True
    >>> {f: True} is not 'an error either'
    True

When Python inserts or looks up a
:class:`frozenbidict <bidict.frozenbidict>`
in a set or mapping, it calls its
:attr:`__hash__ <bidict.FrozenBidictBase.__hash__>` method.
By default, the first call to
:attr:`__hash__ <bidict.FrozenBidictBase.__hash__>`
has linear time and space complexity
in the number of items
(though the memory allocated is ephemeral
and may be reclaimed immediately after).
The result of the first call is cached
so that future calls run in constant time and space.
You can set
:attr:`_HASH_NITEMS_MAX <bidict.FrozenBidictBase._HASH_NITEMS_MAX>`
to limit the number of items that participate
in influencing the hash value.
You can also override
:attr:`_compute_hash <bidict.frozenbidict._compute_hash>`
in a subclass if greater customization is needed.

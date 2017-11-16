:class:`FrozenBidict <bidict.FrozenBidict>`
-------------------------------------------

Having :class:`bidict.BidirectionalMapping`
extend :class:`collections.abc.Mapping`
rather than :class:`MutableMapping <collections.abc.MutableMapping>`
allows for an *immutable* bidict type to extend from *it*.
This type is called :class:`bidict.FrozenBidict`,
and makes up the other branch of the tree.

As you would expect,
attempting to mutate a FrozenBidict after initializing it causes an error::

    >>> from bidict import FrozenBidict
    >>> f = FrozenBidict({'H': 'hydrogen'})
    >>> f['C'] = 'carbon'
    Traceback (most recent call last):
        ...
    TypeError...

Because it is immutable, :class:`FrozenBidict <bidict.FrozenBidict>`
implements :class:`collections.abc.Hashable`.
Thus it's suitable for insertion into sets or other mappings::

    >>> {f} is not 'an error'
    True
    >>> {f: 1} is not 'an error'
    True

See the :class:`bidict.FrozenBidict` and :class:`bidict.FrozenOrderedBidict`
API documentation for more information on implementation details if necessary.

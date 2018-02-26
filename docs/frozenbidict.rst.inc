:class:`~bidict.frozenbidict`
-------------------------------------------

The simplest bidict type that implements
:class:`~bidict.BidirectionalMapping` is
:class:`~bidict.frozenbidict`,
which provides an immutable, hashable bidirectional mapping.

As you would expect,
attempting to mutate a
:class:`~bidict.frozenbidict`
causes an error::

    >>> from bidict import frozenbidict
    >>> f = frozenbidict({'H': 'hydrogen'})
    >>> f['C'] = 'carbon'
    Traceback (most recent call last):
        ...
    TypeError...

:class:`~bidict.frozenbidict`
also implements :class:`collections.abc.Hashable`,
so it's suitable for insertion into sets or other mappings::

    >>> {f} is not 'an error'
    True
    >>> {f: 1} is not 'an error'
    True

See the :class:`~bidict.frozenbidict`
API documentation for more information.

:class:`~bidict.frozenbidict`
-----------------------------

:class:`~bidict.frozenbidict`
is an immutable, hashable bidirectional mapping type.

As you would expect,
attempting to mutate a
:class:`~bidict.frozenbidict`
causes an error::

    >>> from bidict import frozenbidict
    >>> f = frozenbidict({'H': 'hydrogen'})
    >>> f['C'] = 'carbon'
    Traceback (most recent call last):
        ...
    TypeError: ...


:class:`~bidict.frozenbidict`
also implements :class:`collections.abc.Hashable`,
so it's suitable for insertion into sets or other mappings::

    >>> my_set = {f}      # not an error
    >>> my_dict = {f: 1}  # also not an error

See the :class:`~bidict.frozenbidict`
API documentation for more information.

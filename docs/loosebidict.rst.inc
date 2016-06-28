.. _loosebidict:

``loosebidict``
+++++++++++++++

If you know you're going to want all-
:class:`OVERWRITE <bidict.DuplicationBehavior.OVERWRITE>` behaviors
more often than not,
an alternative to using
:func:`forceput() <bidict.bidict.forceput>`
and
:func:`forceupdate() <bidict.bidict.forceupdate>`
is to use a :class:`loosebidict <bidict.loosebidict>` instead.
:class:`loosebidict <bidict.loosebidict>` ’s
``__setitem__()`` and ``update()``
methods use
:class:`OVERWRITE <bidict.DuplicationBehavior.OVERWRITE>`
behaviors by default::

    >>> from bidict import loosebidict
    >>> b = loosebidict({'one': 1})
    >>> b['two'] = 1  # succeeds, no ValueDuplicationError
    >>> b
    loosebidict({'two': 1})
    >>> b.update({'three': 1})  # ditto
    >>> b
    loosebidict({'three': 1})

As with 
:class:`bidict.bidict <bidict.bidict>`,
:func:`loosebidict.put() <bidict.bidict.put>`
and
:func:`loosebidict.putall() <bidict.bidict.putall>`
still provide per-call overrides for duplication behaviors,
and they all still default to
:class:`RAISE <bidict.DuplicationBehavior.RAISE>`.

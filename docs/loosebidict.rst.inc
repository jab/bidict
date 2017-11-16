.. _loosebidict:

``LooseBidict``
+++++++++++++++

If you know you're going to want all-
:class:`OVERWRITE <bidict.DuplicationBehavior.OVERWRITE>` behaviors
more often than not,
an alternative to using
:func:`forceput() <bidict.bidict.forceput>`
and
:func:`forceupdate() <bidict.bidict.forceupdate>`
is to use a :class:`LooseBidict <bidict.LooseBidict>` instead.
:class:`LooseBidict <bidict.LooseBidict>` ’s
``__setitem__()`` and ``update()``
methods use
:class:`OVERWRITE <bidict.DuplicationBehavior.OVERWRITE>`
behaviors by default::

    >>> from bidict import LooseBidict
    >>> b = LooseBidict({'one': 1})
    >>> b['two'] = 1  # succeeds, no ValueDuplicationError
    >>> b
    LooseBidict({'two': 1})
    >>> b.update({'three': 1})  # ditto
    >>> b
    LooseBidict({'three': 1})

As with
:class:`bidict.bidict <bidict.bidict>`,
:func:`LooseBidict.put() <bidict.bidict.put>`
and
:func:`LooseBidict.putall() <bidict.bidict.putall>`
still provide per-call overrides for duplication behaviors,
and they all still default to
:class:`RAISE <bidict.DuplicationBehavior.RAISE>`.

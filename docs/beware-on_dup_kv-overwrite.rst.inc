Beware ``on_dup_kv=OVERWRITE``
++++++++++++++++++++++++++++++

Beware that ``on_dup_kv=OVERWRITE`` semantics
(which :class:`LooseBidict <bidict.LooseBidict>` uses by default)
cause the following potentially surprising behavior::

    >>> from bidict import LooseBidict
    >>> b = LooseBidict({'one': 1, 'two': 2})
    >>> b['one'] = 2
    >>> b
    LooseBidict({'one': 2})

That is, setting an existing key to the value of a different existing item
causes both existing items to be collapsed into a single item.

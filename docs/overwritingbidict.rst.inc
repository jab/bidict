.. _overwritingbidict:

``OverwritingBidict`` Recipe
############################

If you'd like
:attr:`~bidict.OVERWRITE`
to be the default duplication policy for
:func:`~bidict.bidict.__setitem__` and
:func:`~bidict.bidict.update`,
rather than always having to use
:func:`~bidict.bidict.forceput` and
:func:`~bidict.bidict.forceupdate`,
you can use the following recipe::

    >>> from bidict import bidict, OVERWRITE

    >>> class OverwritingBidict(bidict):
    ...     on_dup_val = OVERWRITE

    >>> b = OverwritingBidict({'one': 1})
    >>> b['two'] = 1  # succeeds, no ValueDuplicationError
    >>> b
    OverwritingBidict({'two': 1})

    >>> b.update({'three': 1})  # ditto
    >>> b
    OverwritingBidict({'three': 1})

As with
:class:`bidict.bidict`,
``OverwritingBidict.put()`` and
``OverwritingBidict.putall()``
will still provide per-call overrides for duplication policies,
and will both still default to raising for all duplication types
unless you override those methods too.

To make an overwriting *ordered* bidict,
simply adapt this recipe to have the class inherit from
:class:`bidict.OrderedBidict`.


Beware of ``OVERWRITE``
:::::::::::::::::::::::

With a default :attr:`~bidict.OVERWRITE` policy
as in the ``OverwritingBidict`` recipe above,
beware of the following potentially surprising behavior::

    >>> b = OverwritingBidict({'one': 1, 'two': 2})
    >>> b['one'] = 2
    >>> b
    OverwritingBidict({'one': 2})

That is, setting an existing key to the value of a different existing item
causes both existing items to be collapsed into a single item.

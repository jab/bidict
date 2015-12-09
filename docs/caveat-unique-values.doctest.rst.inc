.. _caveat-unique-values:

Values Must Be Unique
---------------------

Consider the following::

    >>> from bidict import bidict
    >>> b = bidict({0: 0, 1: 1})
    >>> b[0] = 1  # doctest: +SKIP

What should happen next?

If the bidict allowed this to succeed,
because of the uniqueness-of-values constraint,
it would silently clobber both of the existing mappings,
possibly unbeknownst to you,
resulting in surprises or problems down the line.

Instead, bidict raises an exception
any time you attempt to insert a non-unique value,
so you have an opportunity to catch this early
and resolve the conflict before it causes problems later on::

    >>> b = bidict({1: 1})
    >>> b[2] = 1
    Traceback (most recent call last):
        ...
    ValueExistsException: Value 1 exists for key 1

The same thing happens with initializations and
:attr:`update <bidict.bidict.update>` calls
that would overwrite the key of an existing value::

    >>> b = bidict({1: 1, 2: 1})
    Traceback (most recent call last):
        ...
    ValueExistsException: Value 1 exists for key 1
    >>> b = bidict({1: 1})
    >>> b.update({2: 1})
    Traceback (most recent call last):
        ...
    ValueExistsException: Value 1 exists for key 1

You can use
:attr:`forceput <bidict.bidict.forceput>` and
:attr:`forceupdate <bidict.bidict.forceupdate>`
to explicitly opt out of unique value checking::

    >>> b = bidict({0: 0, 1: 1})
    >>> b.forceput(0, 1)
    >>> b
    bidict({0: 1})
    >>> b.forceupdate({1: 1})
    >>> b
    bidict({1: 1})

or use a :class:`loosebidict <bidict.loosebidict>` instead::

    >>> from bidict import loosebidict
    >>> b = loosebidict({0: 0, 1: 1})
    >>> b[0] = 1
    >>> b
    loosebidict({0: 1})
    >>> b.update([(1, 1), (2, 2), (1, 2)])
    >>> b
    loosebidict({1: 2})

The purpose of this is to be more in line with the
`Zen of Python <https://www.python.org/dev/peps/pep-0020/>`_,
which advises,

::

    Errors should never pass silently.
    Unless explicitly silenced.

Note, however, that setting an existing key to a new value
does *not* cause an error,
and is considered an intentional overwrite,
in keeping with dict's behavior::

    >>> b = bidict({1: 1})
    >>> b[1] = 2  # succeeds
    >>> b
    bidict({1: 2})
    >>> b.update([(1, 3), (1, 4), (1, 5)])
    >>> b
    bidict({1: 5})
    >>> bidict([(1, 1), (1, 2)])
    bidict({1: 2})

If you need to guard against accidentally overwriting an existing key's value,
you can either check for its presence first::

    >>> b = bidict({1: 1})
    >>> if 1 not in b:
    ...     b[1] = 2

or you can invert the mapping(s) and perform the same operation on
:attr:`b.inv <bidict.BidirectionalMapping.inv>`,
where the unique-value-constraint would kick in,
though this should not be used if it obscures the intention of the code::

    >>> b = bidict({1: 1})
    >>> b.inv[2] = 1
    Traceback (most recent call last):
        ...
    ValueExistsException: Value 1 exists for key 1
    >>> from bidict import inverted
    >>> b.inv.update(inverted([(1, 3), (1, 4), (1, 5)]))
    Traceback (most recent call last):
        ...
    ValueExistsException: Value 1 exists for key 1
    >>> bidict(inverted([(1, 1), (1, 2)]))
    Traceback (most recent call last):
        ...
    ValueExistsException: Value 1 exists for key 1

The :func:`inverted <bidict.util.inverted>` iterator will be covered further
in a subsequent section.

.. _caveat-unique-values:

Values Must Be Unique
---------------------

Consider the following::

    >>> from bidict import bidict
    >>> b = bidict({1: 1})
    >>> b[2] = 1  # doctest: +SKIP

What should happen next?

If the bidict allowed this to succeed,
because of the uniqueness-of-values constraint,
it would silently clobber the existing mapping,
possibly unbeknownst to the user,
resulting in an unpleasant surprise later on.

Instead, bidict raises an exception
so the user has an opportunity to catch this early
and resolve the conflict before it's too late:

    >>> b = bidict({1: 1})
    >>> b[2] = 1
    Traceback (most recent call last):
        ...
    ValueExistsException: (1, 1)

The same thing happens with offending initializations and updates::

    >>> b = bidict({1: 1, 2: 1})
    Traceback (most recent call last):
        ...
    ValueExistsException: (1, 1)
    >>> b = bidict({1: 1})
    >>> b.update({2: 1})
    Traceback (most recent call last):
        ...
    ValueExistsException: (1, 1)

You can use :attr:`bidict.bidict.forceput` and :attr:`bidict.bidict.forceupdate`
to explicitly opt out of unique value checking::

    >>> b = bidict({1: 1})
    >>> b.forceput(2, 1)
    >>> b
    bidict({2: 1})
    >>> b.forceupdate({3: 1})
    >>> b
    bidict({3: 1})

or use a :class:`bidict.loosebidict` instead (covered ahead).

As the
`Zen of Python <https://www.python.org/dev/peps/pep-0020/>`_
advises,

::

    Errors should never pass silently.
    Unless explicitly silenced.

Note that setting an existing key to a new value
is considered an intentional overwrite
and does not cause an error,
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

If you'd like an error to be thrown in these cases instead,
you can perform the inverse operations on ``b.inv``::

    >>> b = bidict({1: 1})
    >>> b.inv[2] = 1
    Traceback (most recent call last):
        ...
    ValueExistsException: (1, 1)
    >>> from bidict import inverted
    >>> b.inv.update(inverted([(1, 3), (1, 4), (1, 5)]))
    Traceback (most recent call last):
        ...
    ValueExistsException: (1, 1)
    >>> bidict(inverted([(1, 1), (1, 2)]))
    Traceback (most recent call last):
        ...
    ValueExistsException: (1, 1)

.. _equiv-but-distinct:

Equivalent but distinct :class:`~collections.abc.Hashable`\s
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Consider the following::

    >>> d = {1: int, 1.0: float}

How many items do you expect *d* to contain?
The actual result might surprise you::

    >>> len(d)
    1

And similarly,

    >>> dict([(1, int), (1.0, float), (1+0j, complex), (True, bool)])
    {1: <... 'bool'>}
    >>> 1.0 in {True}
    True

(Note that ``1 == 1.0 == 1+0j == True``.)

This illustrates that a mapping cannot contain two items
with equivalent but distinct keys
(and likewise a set cannot contain two equivalent but distinct elements).
If an object that is being looked up in a set or mapping
is equal to a contained object,
the contained object will be found,
even if it is distinct.

With bidict,
since values function as keys in the inverse mapping,
this behavior occurs in the inverse direction too::

    >>> from bidict import bidict
    >>> b = bidict({1: 1.0})
    >>> b.inv[True]
    1
    >>> b[2] = True
    Traceback (most recent call last):
       ...
    ValueDuplicationError: 1.0

Different Values, Same Hash
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Consider the following::

    >>> d = {1: 'one'}
    >>> d[1.0] = 'one point oh'

What do you expect to happen next?
If you expected *d* to become *{1: 'one', 1.0: 'one point oh'}*,
the actual result might surprise you::

    >>> d
    {1: 'one point oh'}

Unfazed? How about this::

    >>> d[True] = 'true'
    >>> d
    {1: 'true'}
    >>> d = dict([(1, 'one'), (1.0, 'one point oh'), (1+0j, 'imaginary!'), (True, 'true')])
    >>> d
    {1: 'true'}

Kudos if this behavior is old hat to you.
Otherwise, take heed:
In Python,
these equivalent values all have the same hash value,
and therefore can only occupy the same single spot
in a set or dictionary::

    >>> hash(1) == hash(1.0) == hash(1+0j) == hash(True)
    True
    >>> hash(0) == hash(0.0) == hash(0j) == hash(False)
    True
    >>> len({0, 0.0, 0j, False})
    1

As demonstrated above,
mutating operations using a (hash-)equivalent but not identical key are
type-insensitive but type-preserving with respect to the existing key.

With bidict,
since values function like keys in the inverse mapping,
the implications of this behavior apply on both sides.
For example::

    >>> from bidict import bidict
    >>> b = bidict({1: 1})
    >>> b.inv[True]
    1
    >>> b[2] = True
    Traceback (most recent call last):
       ...
    ValueDuplicationError: 1
    >>> b.put(True, 'true')
    Traceback (most recent call last):
       ...
    KeyDuplicationError: 1

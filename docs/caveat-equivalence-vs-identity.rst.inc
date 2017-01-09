Equivalence vs. Identity
^^^^^^^^^^^^^^^^^^^^^^^^

Consider the following::

    >>> d = dict([(1, 'int'), (1.0, 'float')])

How many items do you expect *d* to contain?
If you expected *d* to be *{1: 'int', 1.0: 'float'}*,
the actual result might surprise you::

    >>> d
    {1: 'float'}

And similarly,

    >>> dict([(1, 'int'), (1.0, 'float'), (1+0j, 'complex'), (True, 'bool')])
    {1: 'bool'}
    >>> set([True, 1+0j, 1.0, 1])  # doctest: +SKIP
    {True}
    >>> 1.0 in {True}
    True

(Note that ``1 == 1.0 == 1+0j == True``.)

This illustrates that a mapping cannot contain two items
with equivalent but distinct keys
(and likewise a set cannot contain two equivalent but distinct elements).
If an object being looked up in a set or mapping
is equal to a contained object,
the contained object will be found,
even if it is distinct.

With bidict,
since values function as keys in the inverse mapping,
this behavior occurs on both sides::

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

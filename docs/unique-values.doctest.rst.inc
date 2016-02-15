.. _unique-values:

Uniqueness of Values
++++++++++++++++++++

As we know,
in a bidirectional map,
not only must keys be unique,
but values must be unique as well.
This has immediate implications for bidict's API.

Consider the following::

    >>> from bidict import bidict
    >>> b = bidict({'one': 1})
    >>> b['two'] = 1  # doctest: +SKIP

What should happen next?

If the bidict allowed this to succeed,
because of the uniqueness-of-values constraint,
it would silently clobber the existing mapping,
resulting in::

    >>> b  # doctest: +SKIP
    bidict({'two': 1})

This could easily result in surprises or problems down the line.

Instead, bidict raises a
:class:`ValueExistsException <bidict.ValueExistsException>`
so you have an opportunity to catch this early
and resolve the conflict before it causes problems later on::

    >>> b['two'] = 1
    Traceback (most recent call last):
        ...
    ValueExistsException: Value 1 exists with key 'one'

The same thing happens with initializations and
:attr:`update <bidict.bidict.update>` calls
that would overwrite the key of an existing value::

    >>> b = bidict([('one', 1), ('two', 1)])
    Traceback (most recent call last):
        ...
    NonuniqueValuesException: ...
    >>> b = bidict({'one': 1})
    >>> b.update({'two': 1})
    Traceback (most recent call last):
        ...
    ValuesExistException: ...

The purpose of this is to be more in line with the
`Zen of Python <https://www.python.org/dev/peps/pep-0020/>`_,
which advises,

::

    Errors should never pass silently.
    Unless explicitly silenced.

Note that setting an existing key to a new value
does *not* cause an error,
and is considered an intentional overwrite,
in keeping with dict's behavior::

    >>> b = bidict({'one': 1})
    >>> b['one'] = 2  # succeeds
    >>> b
    bidict({'one': 2})
    >>> b.update([('one', 3), ('one', 4), ('one', 5)])
    >>> b
    bidict({'one': 5})
    >>> bidict([('one', 1), ('one', 2)])
    bidict({'one': 2})

Also note that :attr:`update <bidict.bidict.update>` calls are atomic.
That is, if the call results in an exception,
you can be sure that none of the specified items were added::

    >>> b = bidict({'one': 1})
    >>> b.update([('two', 2), ('uno', 1)])
    Traceback (most recent call last):
        ...
    ValuesExistException: ...
    >>> b  # note that ('two', 2) was not added because the call failed:
    bidict({'one': 1})

To customize the default behavior when a key or value already exists,
use :attr:`put <bidict.bidict.put>`
instead of :attr:`__setitem__ <bidict.bidict.__setitem__>`,
and instead of :attr:`update <bidict.bidict.update>`,
use :attr:`putall <bidict.bidict.putall>` (which is also atomic).
These methods allow you to specify different strategies for handling
key collisions (*key_clbhv*) and value collisions (*val_clbhv*).
Possible options are
:class:`IGNORE <bidict.CollisionBehavior.RAISE>`,
:class:`IGNORE <bidict.CollisionBehavior.OVERWRITE>`, and
:class:`IGNORE <bidict.CollisionBehavior.IGNORE>`::

    >>> from bidict import RAISE, IGNORE
    >>> b = bidict({2: 4})
    >>> b.put(2, 8, key_clbhv=RAISE, val_clbhv=IGNORE)
    Traceback (most recent call last):
        ...
    KeyExistsException: Key 2 exists with value 4
    >>> b.putall(RAISE, IGNORE, [(5, 10), (5, 25)])
    Traceback (most recent call last):
        ...
    NonuniqueKeysException: ...
    >>> b.putall(RAISE, IGNORE, [(3, 9), (2, 8)])
    Traceback (most recent call last):
        ...
    KeysExistException: ...
    >>> b  # note that (3, 9) was not added because the call failed:
    bidict({2: 4})
    >>> b.putall(RAISE, IGNORE, {3: 9, 1: 4})
    >>> sorted(b.items())  # note that (1, 4) is ignored, as per val_clbhv
    [(2, 4), (3, 9)]

*key_clbhv* and *val_clbhv* default to *RAISE* for both methods.

You can also use
:attr:`forceput <bidict.bidict.forceput>` and
:attr:`forceupdate <bidict.bidict.forceupdate>`
to explicitly overwrite existing keys and values::

    >>> b = bidict({'one': 1})
    >>> b.forceput('two', 1)
    >>> b
    bidict({'two': 1})
    >>> b.forceupdate({'three': 1})
    >>> b
    bidict({'three': 1})

To always opt out of uniqueness checking,
you can use a :class:`loosebidict <bidict.loosebidict>`, whose
:attr:`__setitem__ <bidict.loosebidict.__setitem__>` and
:attr:`update <bidict.loosebidict.update>`
methods always overwrite existing keys and values,
and whose :attr:`put <bidict.loosebidict.put>`
method defaults to key- and value-overwriting behavior::

    >>> from bidict import loosebidict
    >>> b = loosebidict({'one': 1})
    >>> b['two'] = 1
    >>> b
    loosebidict({'two': 1})
    >>> b.update({'three': 1})
    >>> b
    loosebidict({'three': 1})
    >>> b.put('four', 1)
    >>> b
    loosebidict({'four': 1})

Beware that these semantics enable the following often surprising behavior::

    >>> b = loosebidict({'one': 1, 'two': 2})
    >>> b['one'] = 2
    >>> b
    loosebidict({'one': 2})

That is, setting an existing key to the value of a different existing mapping
in a loosebidict causes both mappings to be collapsed into one.

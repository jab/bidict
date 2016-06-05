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
it would silently clobber the existing item,
resulting in::

    >>> b  # doctest: +SKIP
    bidict({'two': 1})

This could result in surprises or problems down the line.

Instead, bidict raises a
:class:`ValueExistsError <bidict.ValueExistsError>`
so you have an opportunity to catch this early
and resolve the conflict before it causes problems later on::

    >>> b['two'] = 1
    Traceback (most recent call last):
        ...
    ValueExistsError: Value 1 exists with key 'one'

The purpose of this is to be more in line with the
`Zen of Python <https://www.python.org/dev/peps/pep-0020/>`_,
which advises,

::

    Errors should never pass silently.
    Unless explicitly silenced.

Similarly, initializations and :func:`update() <bidict.bidict.update>` calls
that would overwrite the key of an existing value
raise an exception too::

    >>> b = bidict({'one': 1})
    >>> b.update([('two', 2), ('three', 3), ('uno', 1)])
    Traceback (most recent call last):
        ...
    ValueExistsError: Value 1 exists with key 'one'

If an update() call raises,
you can be sure that none of the supplied items were inserted::

    >>> b
    bidict({'one': 1})

Setting an existing key to a new value
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

Duplication of keys or values *within* a supplied update
is also checked for and processed accordingly::

    >>> b.update([('one', 1), ('one', 'uno')])  # duplicate key, unique values
    >>> b  # last item wins:
    bidict({'one': 'uno'})
    >>> b.update([('two', 2), ('dos', 2)])  # unique keys, duplicate values
    Traceback (most recent call last):
        ...
    ValueNotUniqueError: 2

In summary,
when attempting to insert an item with a duplicate key,
bidict's default behavior is to allow the insertion.
When attempting to insert an item with a duplicate value,
bidict's default behavior is to raise.

To customize this default behavior,
use :func:`put() <bidict.bidict.put>`
instead of :func:`__setitem__() <bidict.bidict.__setitem__>`,
and use :func:`putall() <bidict.bidict.putall>`
instead of :func:`update() <bidict.bidict.update>`.
These methods allow you to specify different strategies for handling
key and value duplication via the *on_dup_key* and *on_dup_val* arguments.
Possible options are
:class:`RAISE <bidict.DuplicationBehavior.RAISE>`,
:class:`OVERWRITE <bidict.DuplicationBehavior.OVERWRITE>`, and
:class:`IGNORE <bidict.DuplicationBehavior.IGNORE>`.
:func:`putall() <bidict.bidict.putall>` also accepts a *precheck* positional arg,
which allows you to control whether the given items should be processed for
duplication in their entirety before any of them are inserted::

    >>> from bidict import RAISE, IGNORE
    >>> b = bidict({2: 4})
    >>> b.put(2, 8, on_dup_key=RAISE, on_dup_val=IGNORE)
    Traceback (most recent call last):
        ...
    KeyExistsError: Key 2 exists with value 4
    >>> b.putall(RAISE, IGNORE, True, [(3, 9), (2, 8)])
    Traceback (most recent call last):
        ...
    KeyExistsError: Key 2 exists with value 4
    >>> b  # Note (3, 9) not added b/c call failed and we gave precheck=True:
    bidict({2: 4})
    >>> b.putall(RAISE, IGNORE, True, {3: 9, 1: 4})
    >>> sorted(b.items())  # Note (1, 4) ignored b/c we gave on_dup_val=IGNORE:
    [(2, 4), (3, 9)]

Note: The *on_dup_key* and *on_dup_val* keyword arguments
of :func:`put() <bidict.bidict.put>`
both default to *RAISE*,
providing a more-conservative-by-default alternative to
:func:`__setitem__() <bidict.bidict.__setitem__>`.

As with :func:`update() <bidict.bidict.update>`,
with :func:`putall() <bidict.bidict.putall>`,
the duplication behaviors apply not only
with respect to existing items,
but also with respect to the items to add::

    >>> 5 not in b
    True
    >>> b.putall(RAISE, RAISE, True, [(5, 10), (5, 25)])
    Traceback (most recent call last):
        ...
    KeyNotUniqueError: 5
    >>> 16 not in b.inv
    True
    >>> b.putall(RAISE, RAISE, True, [(4, 16), (8, 16)])
    Traceback (most recent call last):
        ...
    ValueNotUniqueError: 16

Note that if an entire *(k, v)* item in the update is duplicated
elsewhere in the update
or is already in the bidict,
the entire item will just be ignored,
no matter what the key and value duplication behaviors are set to.
The insertion of a duplicate item is construed as a no-op::

    >>> b.putall(RAISE, RAISE, True, [(4, 16), (4, 16)])
    >>> sorted(b.items())
    [(2, 4), (3, 9), (4, 16)]
    >>> b.putall(RAISE, RAISE, True, [(4, 16)])
    >>> sorted(b.items())
    [(2, 4), (3, 9), (4, 16)]

You can also use
:func:`forceput() <bidict.bidict.forceput>` and
:func:`forceupdate() <bidict.bidict.forceupdate>`
to explicitly overwrite existing keys and values::

    >>> b = bidict({'one': 1})
    >>> b.forceput('two', 1)
    >>> b
    bidict({'two': 1})
    >>> b.forceupdate({'three': 1})
    >>> b
    bidict({'three': 1})

Or you can use a :class:`loosebidict <bidict.loosebidict>`, whose
:func:`__setitem__() <bidict.loosebidict.__setitem__>`,
:func:`put() <bidict.loosebidict.put>`, and
:func:`update() <bidict.loosebidict.update>`
methods use *OVERWRITE* behaviors by default::

    >>> from bidict import loosebidict
    >>> b = loosebidict({'one': 1})
    >>> b['two'] = 1
    >>> b
    loosebidict({'two': 1})
    >>> b.put('three', 1)
    >>> b
    loosebidict({'three': 1})
    >>> b.update({'four': 1})
    >>> b
    loosebidict({'four': 1})

Beware that *OVERWRITE* semantics cause
the following potentially surprising behavior::

    >>> b = loosebidict({'one': 1, 'two': 2})
    >>> b['one'] = 2
    >>> b
    loosebidict({'one': 2})

That is, setting an existing key to the value of a different existing item
with *OVERWRITE* behavior causes both existing items to be collapsed into
a single new one.

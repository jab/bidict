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
:class:`ValueNotUniqueError <bidict.ValueNotUniqueError>`
so you have an opportunity to catch this early
and resolve the conflict before it causes problems later on::

    >>> b['two'] = 1
    Traceback (most recent call last):
        ...
    ValueNotUniqueError: ('two', 1) duplicates value in item: ('one', 1)

The purpose of this is to be more in line with the
`Zen of Python <https://www.python.org/dev/peps/pep-0020/>`_,
which advises,

| *Errors should never pass silently.*
| *Unless explicitly silenced.*

Similarly, initializations and :func:`update() <bidict.bidict.update>` calls
that would overwrite the key of an existing value
raise an exception too::

    >>> b = bidict({'one': 1})
    >>> b.update([('two', 2), ('three', 3), ('uno', 1)])
    Traceback (most recent call last):
        ...
    ValueNotUniqueError: ('uno', 1) duplicates value in item: ('one', 1)

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

Duplication of keys or values ``within`` a supplied update
is also checked for and processed accordingly::

    >>> b.update([('one', 1), ('one', 'uno')])  # duplicate key, unique values
    >>> b  # last item wins:
    bidict({'one': 'uno'})
    >>> b.update([('two', 2), ('dos', 2)])  # unique keys, duplicate values
    Traceback (most recent call last):
        ...
    ValueNotUniqueError: ('dos', 2) duplicates value in item: ('two', 2)

In summary,
when attempting to insert an item whose key duplicates an existing item's,
bidict's default behavior is to allow the insertion,
overwriting the existing item with the new one.
When attempting to insert an item whose value duplicates an existing item's,
bidict's default behavior is to raise.
This design naturally falls out of the behavior of Python's built-in dict,
and protects against unexpected data loss.

To customize this default behavior,
use :func:`put() <bidict.bidict.put>`
instead of :func:`__setitem__() <bidict.bidict.__setitem__>`,
and use :func:`putall() <bidict.bidict.putall>`
instead of :func:`update() <bidict.bidict.update>`.
These methods allow you to specify different strategies for handling
key and value duplication via
the ``on_dup_key``, ``on_dup_val``, and ``on_dup_kv`` arguments.
Possible options are
:class:`RAISE <bidict.DuplicationBehavior.RAISE>`,
:class:`OVERWRITE <bidict.DuplicationBehavior.OVERWRITE>`, and
:class:`IGNORE <bidict.DuplicationBehavior.IGNORE>`::

    >>> from bidict import RAISE, IGNORE
    >>> b = bidict({2: 4})
    >>> b.put(2, 8, on_dup_key=RAISE, on_dup_val=IGNORE)
    Traceback (most recent call last):
        ...
    KeyNotUniqueError: (2, 8) duplicates key in item: (2, 4)
    >>> b.putall([(3, 9), (2, 8)], on_dup_key=RAISE, on_dup_val=IGNORE)
    Traceback (most recent call last):
        ...
    KeyNotUniqueError: (2, 8) duplicates key in item: (2, 4)
    >>> b  # Note that (3, 9) was not added because the call failed:
    bidict({2: 4})
    >>> b.putall({3: 9, 1: 4}, on_dup_key=RAISE, on_dup_val=IGNORE)
    >>> sorted(b.items())  # Note (1, 4) was ignored as per on_dup_val=IGNORE:
    [(2, 4), (3, 9)]

Note: The ``on_dup_key``, ``on_dup_val``, and ``on_dup_kv`` keyword arguments of
:func:`put() <bidict.bidict.put>`
and
:func:`putall() <bidict.bidict.putall>`
all default to ``RAISE``,
providing more-conservative-by-default alternatives to
:func:`__setitem__() <bidict.bidict.__setitem__>`
and
:func:`update() <bidict.bidict.update>`.

As with :func:`update() <bidict.bidict.update>`,
with :func:`putall() <bidict.bidict.putall>`,
the duplication behaviors apply not only
with respect to duplication of existing items,
but also with respect to duplication within the given items::

    >>> 5 not in b
    True
    >>> b.putall([(5, 10), (5, 25)])
    Traceback (most recent call last):
        ...
    KeyNotUniqueError: (5, 25) duplicates key in item: (5, 10)
    >>> 16 not in b.inv
    True
    >>> b.putall([(4, 16), (8, 16)])
    Traceback (most recent call last):
        ...
    ValueNotUniqueError: (8, 16) duplicates value in item: (4, 16)

Note that it's possible for a given item to duplicate
the key of a previously given (or existing) item,
and the value of another previously given (or existing) item.
This is where ``on_dup_kv`` comes in::

    >>> b.putall([(4, 16), (5, 25), (4, 25)],
    ...          on_dup_key=IGNORE, on_dup_val=IGNORE, on_dup_kv=RAISE)
    Traceback (most recent call last):
        ...
    KeyAndValueNotUniqueError: (4, 25) duplicates key and value in items: (4, 16), (5, 25)

Because the given ``on_dup_key`` and ``on_dup_val`` behaviors may differ,
``on_dup_kv`` allows you to indicate how you want to handle this case
without ambiguity.

Note that if an entire ``(k, v)`` item in the update is duplicated
elsewhere in the update
or is already in the bidict,
the entire item will just be ignored,
no matter what the key and value duplication behaviors are set to.
The insertion of a duplicate item is construed as a no-op::

    >>> b.putall([(4, 16), (4, 16)])
    >>> sorted(b.items())
    [(2, 4), (3, 9), (4, 16)]
    >>> b.putall([(4, 16)])
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

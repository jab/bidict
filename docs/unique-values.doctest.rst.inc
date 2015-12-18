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

    >>> b = bidict({'one': 1, 'two': 1})
    Traceback (most recent call last):
        ...
    ValueExistsException: Value 1 exists with key...
    >>> b = bidict({'one': 1})
    >>> b.update({'two': 1})
    Traceback (most recent call last):
        ...
    ValueExistsException: Value 1 exists with key 'one'

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

To ensure uniqueness of both the value and the key before inserting them,
use :attr:`put <bidict.bidict.put>`
instead of :attr:`__setitem__ <bidict.bidict.__setitem__>`,
which raises a
:class:`KeyExistsException <bidict.KeyExistsException>`
or a
:class:`ValueExistsException <bidict.ValueExistsException>`
if the key or value being inserted is not unique::

    >>> b = bidict({'one': 1})
    >>> b.put('one', 2)
    Traceback (most recent call last):
        ...
    KeyExistsException: Key 'one' exists with value 1
    >>> b.put('two', 1)
    Traceback (most recent call last):
        ...
    ValueExistsException: Value 1 exists with key 'one'

To explicitly opt out of unique value checking,
You can use
:attr:`forceput <bidict.bidict.forceput>` and
:attr:`forceupdate <bidict.bidict.forceupdate>`::

    >>> b = bidict({'one': 1})
    >>> b.forceput('two', 1)
    >>> b
    bidict({'two': 1})
    >>> b.forceupdate({'three': 1})
    >>> b
    bidict({'three': 1})

Or to explicitly opt out of all uniqueness checking,
you can instead use a :class:`loosebidict <bidict.loosebidict>`,
whose default semantics are to always overwrite existing mappings
with whatever new ones are given::

    >>> from bidict import loosebidict
    >>> b = loosebidict({'one': 1})
    >>> b['two'] = 1
    >>> b
    loosebidict({'two': 1})
    >>> b.update({'three': 1})
    >>> b
    loosebidict({'three': 1})

Beware that these semantics enable the following often surprising behavior::

    >>> b = loosebidict({'one': 1, 'two': 2})
    >>> b['one'] = 2
    >>> b
    loosebidict({'one': 2})

That is, setting an existing key to the value of a different existing mapping
in a loosebidict causes both mappings to be collapsed into one.

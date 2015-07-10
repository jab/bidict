None Breaks the Slice Syntax
----------------------------

When you use the slice syntax,
under the hood
Python creates a :class:`slice` object that it passes into bidict's
:attr:`bidict.BidirectionalMapping.__getitem__` method.
A call like ``b[:'foo']`` causes a ``slice(None, 'foo', None)`` to be created.
A call like ``b['foo':]`` causes a ``slice('foo', None, None)`` to be created.

Consider the following::

    >>> b = bidict(foo=None)
    >>> b[:None]

In a just world,
this would give back ``'foo'``,
the key which maps to the value ``None``.
But when a bidict gets the slice object Python passes it,
all it sees is ``slice(None, None, None)``,
so it can't tell whether you wrote
``b[:None]``,
referring to an inverse mapping,
or
``b[None:]``,
referring to a forward mapping
(or for that matter ``b[:]``).

In this case,
lacking any known good alternatives,
bidict currently throws a :class:`TypeError`,
which unfairly puts the burden of disambiguation on the user
for something that was unambiguous to the user in the first place.

The upshot of this is
if you will be storing ``None`` as a key (or value) in a bidict,
and need to look up the value (or key) it maps to,
you can't use the slice syntax.
Instead you have to do something like::

    >>> b.inv[None]
    'foo'

Ideas have been explored to make this edge case work
but no robust solutions have been found.
The limits of Python syntax hacks.
Faugh!

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
``b[None:]``, referring to a forward mapping,
``b[:None]``, referring to an inverse mapping,
or for that matter ``b[:]``,
which wouldn't be meaningful at all.

In this case,
on Python 2, where forward and inverse slices have different opcodes,
bidict resorts to stack inspection
to try to guess what the user actually wrote.
This currently only works when there's only one slice on the line
which originated the bidict's getitem call,
so e.g. ``b[:None] + 'foo'`` will work fine, but::

    >>> b[:None] + ['foo'][0:][0]
    Traceback (most recent call last):
    ...
    TypeError: Could not disambiguate None-slice

On Python 3,
lacking any known good alternatives,
a valid None slice currently results in a :class:`TypeError`,
just as if the user had written an invalid slice like ``b[:]``.

So, if you will be storing ``None`` as a key (or value) in a bidict,
and need to look up the value (or key) it maps to
either on Python 3 or on a line with another slice,
you can't use the slice syntax.
Instead you have to do something like::

    >>> b.inv[None]
    'foo'

This unfairly puts the burden of disambiguation on the user
for something that was unambiguous to the user in the first place.

Definitely interested in a more robust solution to this edge case
if a reasonably practical one can be found.
Suggestions very much appreciated.

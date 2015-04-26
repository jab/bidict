.. _basic-usage:

Basic Usage
-----------

Let's return to the example from the :ref:`intro`::

    >>> element_by_symbol = bidict(H='hydrogen')

As we saw, we can use standard dict getitem (bracket) syntax
to reference a forward mapping ``d[key]``,
and slice syntax to reference an inverse mapping ``d[:value]``.
The slice syntax works for setting and deleting items too::

    >>> element_by_symbol[:'helium'] = 'He'
    >>> del element_by_symbol[:'hydrogen']
    >>> element_by_symbol
    bidict({'He': 'helium'})

The rest of the
`MutableMapping ABC <https://docs.python.org/3/library/collections.abc.html#collections.abc.MutableMapping>`_
is also supported::

    >>> 'C' in element_by_symbol
    False
    >>> element_by_symbol.get('C', 'carbon')
    'carbon'
    >>> element_by_symbol.pop('He')
    'helium'
    >>> element_by_symbol
    bidict({})
    >>> element_by_symbol.update(Hg='mercury')
    >>> element_by_symbol
    bidict({'Hg': 'mercury'})

As we saw, we can also use the unary inverse operator ``~``
to reference a bidict's inverse.
This can be handy for composing with other operations::

    >>> 'mercury' in ~element_by_symbol
    True
    >>> (~element_by_symbol).pop('mercury')
    'Hg'

Because inverse mappings are maintained alongside forward mappings,
referencing a bidict's inverse
is always a constant-time operation.
No need to go through the entire map on every reference.

One last thing, bidicts interoperate well with other types of maps.
For example, they support (efficient) polymorphic equality testing::

    >>> bidict(a=1) == dict(a=1)
    True

And converting back and forth works as expected::

    >>> dict(bidict(a=1))
    {'a': 1}
    >>> bidict(dict(a=1))
    bidict({'a': 1})

Straightforward so far?
Hopefully bidict feels right at home
among the Python built-ins you already know.

But read on to make sure you cover some important :ref:`caveats`.

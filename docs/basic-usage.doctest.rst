.. _basic-usage:

Basic Usage
-----------

Let's return to the example from the :ref:`intro`::

    >>> from bidict import bidict
    >>> element_by_symbol = bidict(H='hydrogen')

As we saw, this behaves just like a dict,
but maintains a special :attr:`.inv <bidict.BidirectionalMapping.inv>` property
giving access to inverse mappings::

    >>> element_by_symbol.inv['helium'] = 'He'
    >>> del element_by_symbol.inv['hydrogen']
    >>> element_by_symbol
    bidict({'He': 'helium'})

The rest of the
:class:`collections.abc.MutableMapping` ABC
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
    >>> 'mercury' in element_by_symbol.inv
    True
    >>> element_by_symbol.inv.pop('mercury')
    'Hg'

Because inverse mappings are maintained alongside forward mappings,
referencing a bidict's inverse
is always a constant-time operation.

One last thing, bidicts interoperate well with other types of maps.
For example, they support (efficient) polymorphic equality testing::

    >>> bidict(a=1) == dict(a=1)
    True

And converting back and forth works as expected::

    >>> dict(bidict(a=1))
    {'a': 1}
    >>> bidict(dict(a=1))
    bidict({'a': 1})

Hopefully bidict feels right at home
among the Python built-ins you already know.

But read on to make sure you cover some important :ref:`caveats`.

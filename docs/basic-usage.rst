.. _basic-usage:

Basic Usage
-----------

Let's return to the example from the :ref:`intro`::

    >>> from bidict import bidict
    >>> element_by_symbol = bidict(H='hydrogen')

As we saw, this behaves just like a dict,
but maintains a special
:attr:`~bidict.BidirectionalMapping.inv` attribute
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
    bidict()
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


.. include:: values-hashable.rst.inc

.. include:: values-unique.rst.inc

.. include:: order-matters.rst.inc

.. include:: interop.rst.inc


Hopefully bidict feels right at home
among the Python built-ins you already know.
Proceed to :ref:`other-bidict-types`
for documentation on the remaining bidict flavors.

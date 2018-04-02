Other Functionality
===================

:func:`bidict.pairs`
--------------------

:func:`bidict.pairs` has the same signature as ``dict.__init__()``.
It yields the given (*k*, *v*) pairs
in the same order they'd be processed
if passed into ``dict.__init__()``.

.. code:: python

   >>> from bidict import pairs
   >>> list(pairs({'a': 1}, b=2))
   [('a', 1), ('b', 2)]
   >>> list(pairs([('a', 1), ('b', 2)], b=3))
   [('a', 1), ('b', 2), ('b', 3)]


:func:`bidict.inverted`
-----------------------

bidict provides the :class:`~bidict.inverted` iterator
to help you get inverse pairs from various types of objects.

Pass in a mapping to get the inverse mapping:

.. code:: python

   >>> from bidict import inverted
   >>> it = inverted({1: 'one'})
   >>> {k: v for (k, v) in it}
   {'one': 1}

...an iterable of pairs to get the pairs' inverses:

.. code:: python

   >>> list(inverted([(1, 'one'), (2, 'two')]))
   [('one', 1), ('two', 2)]
   >>> list(inverted((i*i, i) for i in range(2, 5)))
   [(2, 4), (3, 9), (4, 16)]

...or any object implementing an ``__inverted__`` method,
which objects that already know their own inverses (such as bidicts)
can implement themselves:

.. code:: python

   >>> from bidict import bidict, OrderedBidict
   >>> dict(inverted(bidict({1: 'one'})))
   {'one': 1}
   >>> list(inverted(OrderedBidict([(2, 4), (3, 9)])))
   [(4, 2), (9, 3)]


Perhaps you'd be interested in taking a look at the :doc:`addendum` next.

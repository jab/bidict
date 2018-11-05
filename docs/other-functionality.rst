Other Functionality
===================

:func:`bidict.inverted`
-----------------------

bidict provides the :class:`~bidict.inverted` iterator
to help you get inverse items from various types of objects.

Pass in a mapping to get the inverse mapping:

.. doctest::

   >>> from bidict import inverted
   >>> it = inverted({1: 'one'})
   >>> {k: v for (k, v) in it}
   {'one': 1}

...an iterable of pairs to get the pairs' inverses:

.. doctest::

   >>> list(inverted([(1, 'one'), (2, 'two')]))
   [('one', 1), ('two', 2)]
   >>> list(inverted((i*i, i) for i in range(2, 5)))
   [(2, 4), (3, 9), (4, 16)]

...or any object implementing an ``__inverted__`` method,
which objects that already know their own inverses (such as bidicts)
can implement themselves:

.. testsetup::

   from bidict import bidict, OrderedBidict

.. doctest::

   >>> dict(inverted(bidict({1: 'one'})))
   {'one': 1}
   >>> list(inverted(OrderedBidict([(2, 4), (3, 9)])))
   [(4, 2), (9, 3)]


Perhaps you'd be interested in taking a look at the :doc:`addendum` next.

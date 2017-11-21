.. _changelog:

Changelog
=========

.. include:: release-notifications.rst.inc


0.14.0 (not yet released)
-------------------------

- Fix a bug where :class:`bidict <bidict.bidict>`\'s
  default *on_dup_kv* policy was set to
  :class:`RAISE <bidict.DuplicationPolicy.RAISE>`,
  rather than matching whatever *on_dup_val* policy was in effect
  as was :ref:`documented <key-and-value-duplication>`.

- Fix a bug that could happen when using Python's optimization (``-O``) flag
  that could leave an ordered bidict in an inconsistent state
  when dealing with duplicated, overwritten keys or values.
  If you do not use optimizations
  (specifically, skipping ``assert`` statements),
  this would not have affected you.

- Fix a bug introduced by the optimizations in 0.13.0 that could cause
  a frozen bidict that compared equal to another mapping
  to have a different hash value from the other mapping,
  violating Python's object model.
  This would only have affected you if you were inserting a
  frozen bidict and some other immutable mapping that it compared equal to
  into the same set or mapping.

- Add :meth:`equals_order_sensitive()
  <bidict.FrozenOrderedBidict.equals_order_sensitive>`.

- Reduce the memory usage of ordered bidicts.

- Make copying of ordered bidicts faster.

- Improvements to tests and CI, including:

  - Test on Windows
  - Test with PyPy3
  - Test with CPython 3.7-dev
  - Test with optimization flags
  - Require pylint to pass


Breaking API Changes
++++++++++++++++++++

This release includes multiple API simplifications and improvements.

- Rename:

    - ``orderedbidict`` → :class:`OrderedBidict <bidict.OrderedBidict>`
    - ``frozenorderedbidict`` → :class:`FrozenOrderedBidict <bidict.FrozenOrderedBidict>`

  so that these now match the case of :class:`collections.OrderedDict`.

  The names of the
  :class:`bidict <bidict.bidict>`,
  :class:`namedbidict <bidict.namedbidict>`, and
  :class:`frozenbidict <bidict.frozenbidict>` classes
  have been retained as all-lowercase
  so that they continue to match the case of
  :class:`dict`, :func:`namedtuple <collections.namedtuple>`, and
  :class:`frozenset`, respectively.

- The ``ON_DUP_VAL`` duplication policy value for *on_dup_kv* has been removed.
  Use ``None`` instead.

- Merge :class:`frozenbidict <bidict.frozenbidict>` and ``BidictBase``
  together and remove ``BidictBase``.
  :class:`frozenbidict <bidict.frozenbidict>`
  is now the concrete base class that all other bidict types derive from.
  See the updated :ref:`bidict-type-hierarchy`.

- Merge :class:`frozenbidict <bidict.frozenbidict>` and ``FrozenBidictBase``
  together and remove ``FrozenBidictBase``.
  See the updated :ref:`bidict-type-hierarchy`.

- Merge ``frozenorderedbidict`` and ``OrderedBidictBase`` together
  into a single :class:`FrozenOrderedBidict <bidict.FrozenOrderedBidict>`
  class and remove ``OrderedBidictBase``.
  :class:`OrderedBidict <bidict.OrderedBidict>` now extends
  :class:`FrozenOrderedBidict <bidict.FrozenOrderedBidict>`
  to add mutable behavior.
  See the updated :ref:`bidict-type-hierarchy`.

- Make :meth:`(Frozen)OrderedBidict.__eq__() <bidict.FrozenOrderedBidict.__eq__>`
  always perform an order-insensitive equality test,
  even if the other mapping is ordered.

  Previously,
  :meth:`OrderedBidictBase.__eq__() <bidict.FrozenOrderedBidict.__eq__>`
  was only order-sensitive for other ``OrderedBidictBase`` subclasses,
  and order-insensitive otherwise.

  Use the new :meth:`equals_order_sensitive()
  <bidict.FrozenOrderedBidict.equals_order_sensitive>`
  method for order-sensitive equality comparison.

- ``orderedbidict._should_compare_order_sensitive()`` has been removed.

- ``frozenorderedbidict._HASH_NITEMS_MAX`` has been removed.
  Since its hash value must be computed from all contained items
  (so that hash results are consistent with
  equality comparisons against unordered mappings),
  the number of items that influence the hash value should not be limitable.

- ``frozenbidict._USE_ITEMSVIEW_HASH`` has been removed, and
  :meth:`frozenbidict.compute_hash() <bidict.frozenbidict.compute_hash>`
  now uses ``collections.ItemsView._hash()`` to compute the hash always,
  not just when running on PyPy.

  Override :meth:`frozenbidict.compute_hash() <bidict.frozenbidict.compute_hash>`
  to return ``hash(frozenset(iteritems(self)))``
  if you prefer the old default behavior on CPython,
  which takes linear rather than constant space,
  but which uses the ``frozenset_hash`` routine
  (implemented in ``setobject.c``)
  rather than the pure Python ``ItemsView._hash()`` routine.

- ``loosebidict`` and ``looseorderedbidict`` have been removed.
  Simple recipes to implement them yourself are now given in
  :ref:`overwritingbidict`.

- Rename ``FrozenBidictBase._compute_hash()`` →
  :meth:`frozenbidict.compute_hash() <bidict.frozenbidict.compute_hash>`

- Rename ``DuplicationBehavior`` →
  :class:`DuplicationPolicy <bidict.DuplicationPolicy>`.

- Rename:

    - ``bidict.BidictBase._fwd_class`` → :attr:`bidict.frozenbidict.fwd_cls`
    - ``bidict.BidictBase._inv_class`` → :attr:`bidict.frozenbidict.inv_cls`
    - ``bidict.BidictBase._on_dup_key`` → :attr:`bidict.frozenbidict.on_dup_key`
    - ``bidict.BidictBase._on_dup_val`` → :attr:`bidict.frozenbidict.on_dup_val`
    - ``bidict.BidictBase._on_dup_kv`` → :attr:`bidict.frozenbidict.on_dup_kv`


0.13.1 (2017-03-15)
-------------------

- Fix regression introduced by the new
  :meth:`__subclasshook__ <bidict.BidirectionalMapping.__subclasshook__>`
  functionality in 0.13.0 so that
  ``issubclass(OldStyleClass, BidirectionalMapping)`` once again
  works with old-style classes,
  returning ``False`` rather than raising :class:`AttributeError`
  (`thanks, @knaperek <https://github.com/jab/bidict/pull/41>`_).


0.13.0 (2017-01-19)
-------------------

- Support Python 3.6.

  (Earlier versions of bidict should work fine on 3.6, but it is officially
  supported starting in this version.)

- :class:`BidirectionalMapping <bidict.BidirectionalMapping>`
  has been refactored into an abstract base class,
  following the way :class:`collections.abc.Mapping` works.
  The concrete method implementations it used to provide have been moved
  into a new ``BidictBase`` subclass.

  :class:`BidirectionalMapping <bidict.BidirectionalMapping>`
  now also implements
  :meth:`__subclasshook__ <bidict.BidirectionalMapping.__subclasshook__>`,
  so any class that provides a conforming set of attributes
  (enumerated in :attr:`_subclsattrs <bidict.BidirectionalMapping._subclsattrs>`)
  will be considered a
  :class:`BidirectionalMapping <bidict.BidirectionalMapping>`
  subclass automatically.

- ``OrderedBidirectionalMapping`` has been renamed to ``OrderedBidictBase``,
  to better reflect its function. (It is not an ABC.)

- A new ``FrozenBidictBase`` class has been factored out of
  :class:`frozenbidict <bidict.frozenbidict>` and
  :class:`frozenorderedbidict <bidict.FrozenOrderedBidict>`.
  This implements common behavior such as caching the result of
  ``__hash__`` after the first call.

- The hash implementations of
  :class:`frozenbidict <bidict.frozenfidict>` and
  :class:`frozenorderedbidict <bidict.FrozenOrderedBidict>`.
  have been reworked to improve performance and flexibility.
  :class:`frozenorderedbidict <bidict.FrozenOrderedBidict>`\'s
  hash implementation is now order-sensitive.

  See
  :meth:`frozenbidict._compute_hash() <bidict.frozenbidict.compute_hash>` and
  ``frozenorderedbidict._compute_hash``
  for more documentation of the changes,
  including the new
  ``frozenbidict._USE_ITEMSVIEW_HASH`` and
  ``frozenorderedbidict._HASH_NITEMS_MAX``
  attributes.
  If you have an interesting use case that requires overriding these,
  or suggestions for an alternative implementation,
  please `share your feedback <https://gitter.im/jab/bidict>`_.

- Add :attr:`_fwd_class <bidict.frozenbidict.fwd_cls>` and
  :attr:`_inv_class <bidict.frozenbidict.inv_cls>` attributes
  representing the backing :class:`Mapping <collections.abc.Mapping>` types
  used internally to store the forward and inverse dictionaries, respectively.

  This allows creating custom bidict types with extended functionality
  simply by overriding these attributes in a subclass.

  See the new :ref:`extending` documentation for examples.

- Pass any parameters passed to :meth:`bidict.popitem() <bidict.bidict.popitem>`
  through to ``_fwd.popitem`` for greater extensibility.

- More concise repr strings for empty bidicts.

  e.g. ``bidict()`` rather than ``bidict({})`` and
  ``orderedbidict()`` rather than ``orderedbidict([])``.

- Add :attr:`bidict.compat.PYPY` and
  remove unused ``bidict.compat.izip_longest``.

0.12.0 (2016-07-03)
-------------------

- New/renamed exceptions:

  - :class:`KeyDuplicationError <bidict.KeyDuplicationError>`
  - :class:`ValueDuplicationError <bidict.ValueDuplicationError>`
  - :class:`KeyAndValueDuplicationError <bidict.KeyAndValueDuplicationError>`
  - :class:`DuplicationError <bidict.DuplicationError>` (base class for the above)

- :func:`put() <bidict.bidict.put>`
  now accepts ``on_dup_key``, ``on_dup_val``, and ``on_dup_kv`` keyword args
  which allow you to override the default policy
  when the key or value of a given item
  duplicates any existing item's.
  These can take the following values:

  - :attr:`RAISE <bidict.DuplicationPolicy.RAISE>`
  - :attr:`OVERWRITE <bidict.DuplicationPolicy.OVERWRITE>`
  - :attr:`IGNORE <bidict.DuplicationPolicy.IGNORE>`

  ``on_dup_kv`` can also take ``ON_DUP_VAL``.

  If not provided,
  :func:`put() <bidict.bidict.put>` uses the
  :attr:`RAISE <bidict.DuplicationPolicy.RAISE>` policy by default.

- New :func:`putall() <bidict.bidict.putall>` method
  provides a bulk :func:`put() <bidict.bidict.put>` API,
  allowing you to override the default duplication handling policy
  that :func:`update() <bidict.bidict.update>` uses.

- :func:`bidict.update() <bidict.bidict.update>` now fails clean,
  so if an :func:`update() <bidict.bidict.update>` call raises a
  :class:`DuplicationError <bidict.DuplicationError>`,
  you can now be sure that none of the given items was inserted.

  Previously, all of the given items that were processed
  before the one causing the failure would have been inserted,
  and no facility was provided to recover
  which items were inserted and which weren't,
  nor to revert any changes made by the failed
  :func:`update() <bidict.bidict.update>` call.
  The new behavior makes it easier to reason about and control
  the effects of failed :func:`update() <bidict.bidict.update>` calls.

  The new :func:`putall() <bidict.bidict.putall>` method also fails clean.

  Internally, this is implemented by storing a log of changes
  made while an update is being processed, and rolling back the changes
  when one of them is found to cause an error.
  This required reimplementing :class:`orderedbidict <bidict.OrderedBidict>`
  on top of two dicts and a linked list, rather than two OrderedDicts,
  since :class:`OrderedDict <collections.OrderedDict>` does not expose
  its underlying linked list.

- :func:`orderedbidict.move_to_end() <bidict.OrderedBidict.move_to_end>`
  now works on Python < 3.2 as a result of the new
  :class:`orderedbidict <bidict.OrderedBidict>` implementation.

- Add

  - :func:`bidict.compat.viewkeys`
  - :func:`bidict.compat.viewvalues`
  - :func:`bidict.compat.iterkeys`
  - :func:`bidict.compat.itervalues`
  - :func:`bidict.compat.izip`
  - ``bidict.compat.izip_longest``

  to complement the existing
  :func:`iteritems() <bidict.compat.iteritems>` and
  :func:`viewitems() <bidict.compat.viewitems>`
  compatibility helpers.

- More efficient implementations of
  :func:`pairs() <bidict.util.pairs>`,
  :func:`inverted() <bidict.util.inverted>`, and
  :func:`bidict.copy() <bidict.frozenbidict.copy>`.

- Implement :func:`bidict.__copy__() <bidict.frozenbidict.__copy__>`
  for use with the :mod:`copy` module.

- Fix issue preventing a client class from inheriting from ``loosebidict``
  (see `#34 <https://github.com/jab/bidict/issues/34>`_).

- Add benchmarking to tests.

- Drop official support for CPython 3.3.
  (It may continue to work, but is no longer being tested.)

Breaking API Changes
++++++++++++++++++++

- Rename ``KeyExistsException`` to :class:`KeyDuplicationError <bidict.KeyDuplicationError>`
  and ``ValueExistsException`` to :class:`ValueDuplicationError <bidict.ValueDuplicationError>`.

- When overwriting the key of an existing value in an :class:`orderedbidict <bidict.OrderedBidict>`,
  the position of the existing item is now preserved,
  overwriting the key of the existing item in place,
  rather than moving the item to the end.
  This now matches the behavior of overwriting the value of an existing key,
  which has always preserved the position of the existing item.
  (If inserting an item whose key duplicates that of one existing item
  and whose value duplicates that of another,
  the existing item whose value is duplicated is still dropped,
  and the existing item whose key is duplicated
  still gets its value overwritten in place, as before.)

  For example::

      >>> from bidict import orderedbidict  # doctest: +SKIP
      >>> o = orderedbidict([(0, 1), (2, 3)])  # doctest: +SKIP
      >>> o.forceput(4, 1)  # doctest: +SKIP

  previously would have resulted in::

      >>> o  # doctest: +SKIP
      orderedbidict([(2, 3), (4, 1)])

  but now results in::

      >>> o  # doctest: +SKIP
      orderedbidict([(4, 1), (2, 3)])


0.11.0 (2016-02-05)
-------------------

- Add
  :class:`orderedbidict <bidict.OrderedBidict>`,
  ``looseorderedbidict``, and
  :class:`frozenorderedbidict <bidict.FrozenOrderedBidict>`.

- Add :doc:`Code of Conduct <code-of-conduct>`.

- Drop official support for pypy3.
  (It still may work but is no longer being tested.
  Support may be added back once pypy3 has made more progress.)

0.10.0.post1 (2015-12-23)
-------------------------

- Minor documentation fixes and improvements.


0.10.0 (2015-12-23)
-------------------

- Remove several features in favor of keeping the API simpler
  and the code more maintainable.

- In the interest of protecting data safety more proactively, by default
  bidict now raises an error on attempting to insert a non-unique value,
  rather than allowing its associated key to be silently overwritten.
  See discussion in `#21 <https://github.com/jab/bidict/issues/21>`_.

- New :meth:`forceupdate() <bidict.bidict.forceupdate>` method
  provides a bulk :meth:`forceput() <bidict.bidict.forceput>` operation.

- Fix bugs in
  :attr:`pop() <bidict.bidict.pop>` and
  :attr:`setdefault() <bidict.bidict.setdefault>`
  which could leave a bidict in an inconsistent state.

Breaking API Changes
++++++++++++++++++++

- Remove ``bidict.__invert__``, and with it, support for the ``~b`` syntax.
  Use :attr:`b.inv <bidict.frozenbidict.inv>` instead.
  `#19 <https://github.com/jab/bidict/issues/19>`_

- Remove support for the slice syntax.
  Use ``b.inv[val]`` rather than ``b[:val]``.
  `#19 <https://github.com/jab/bidict/issues/19>`_

- Remove ``bidict.invert``.
  Use :attr:`b.inv <bidict.frozenbidict.inv>`
  rather than inverting a bidict in place.
  `#20 <https://github.com/jab/bidict/issues/20>`_

- Raise ``ValueExistsException``
  when attempting to insert a mapping with a non-unique key.
  `#21 <https://github.com/jab/bidict/issues/21>`_

- Rename ``collapsingbidict`` to ``loosebidict``
  now that it suppresses
  ``ValueExistsException``
  rather than the less general ``CollapseException``.
  `#21 <https://github.com/jab/bidict/issues/21>`_

- ``CollapseException`` has been subsumed by
  ``ValueExistsException``.
  `#21 <https://github.com/jab/bidict/issues/21>`_

- :meth:`put() <bidict.bidict.put>` now raises ``KeyExistsException``
  when attempting to insert an already-existing
  key, and ``ValueExistsException`` when
  attempting to insert an already-existing value.


0.9.0.post1 (2015-06-06)
------------------------

- Fix metadata missing in the 0.9.0rc0 release.


0.9.0rc0 (2015-05-30)
---------------------

- Add this changelog,
  `Contributors' Guide <https://github.com/jab/bidict/blob/master/CONTRIBUTING.rst>`_,
  `Gitter chat room <https://gitter.im/jab/bidict>`_,
  and other community-oriented improvements.

- Adopt Pytest (thanks Tom Viner and Adopt Pytest Month).

- Add property-based tests via
  `hypothesis <https://hypothesis.readthedocs.io>`_.

- Other code, tests, and docs improvements.

Breaking API Changes
++++++++++++++++++++

- Move ``bidict.iteritems`` and ``bidict.viewitems``
  to new :mod:`bidict.compat` module.

- Move :class:`bidict.inverted`
  to new :mod:`bidict.util` module
  (still available from top-level :mod:`bidict` module as well).

- Move ``bidict.fancy_iteritems``
  to :func:`bidict.util.pairs`
  (also available from top level as :func:`bidict.pairs`).

- Rename ``bidict_type`` keyword arg to ``base_type``
  in :func:`bidict.namedbidict`.

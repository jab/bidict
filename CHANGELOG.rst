.. _changelog:

Changelog
=========

Release Notifications
---------------------

`Follow bidict on VersionEye <https://www.versioneye.com/python/bidict>`_
to automatically be notified via email
when a new version of bidict is released.

0.12.0-dev (not yet released)
-----------------------------

- :func:`put() <bidict.bidict.put>`
  now accepts ``on_dup_key``, ``on_dup_val``, and ``on_dup_kv`` keyword args
  which allow you to override the default behavior
  when the key and/or value of a given item
  duplicate those/that of any existing item(s).
  These can take the following values:

  - :attr:`bidict.DuplicationBehavior.RAISE`
  - :attr:`bidict.DuplicationBehavior.OVERWRITE`
  - :attr:`bidict.DuplicationBehavior.IGNORE`

  (Note: When you try to insert an item,
  it's possible that its key duplicates the key of one existing item,
  and its value duplicates the value of another existing item.
  Because the given ``on_dup_key`` and ``on_dup_val`` behaviors may differ,
  ``on_dup_kv`` allows you to indicate unambiguously
  how you want to handle this case.)

  If not provided,
  the default value that :func:`bidict.put() <bidict.bidict.put>`
  assigns ``on_dup_key``, ``on_dup_val``, and ``on_dup_kv`` is
  :attr:`RAISE <bidict.DuplicationBehavior.RAISE>`.

  In contrast,
  :func:`bidict.__setitem__() <bidict.bidict.__setitem__>`
  behaves like a :func:`put() <bidict.bidict.put>` call
  with ``on_dup_key=OVERWRITE``, ``on_dup_val=RAISE``, and ``on_dup_kv=RAISE``,
  closely tracking the previous behavior.

  And :class:`loosebidict.__setitem__() <bidict.bidict.__setitem__>`
  behaves like a :class:`put() <bidict.bidict.put>` call
  with all duplication behaviors set to
  :attr:`OVERWRITE <bidict.DuplicationBehavior.OVERWRITE>`,
  tracking the previous behavior.

  In both cases,
  :func:`put() <bidict.bidict.put>`
  still provides a RAISE-on-any-duplication (by default) alternative to
  :func:`__setitem__() <bidict.bidict.__setitem__>`,
  but now allows customizing this behavior via the new keyword arguments.

- New :func:`putall() <bidict.bidict.putall>` method
  provides a bulk :func:`put() <bidict.bidict.put>` API,
  which additionally accepts a ``precheck`` keyword argument (see below).

- :func:`bidict.update() <bidict.bidict.update>` now offers stronger
  consistency guarantees by checking for and handling duplication
  (first within the given items,
  and then between the given items and any existing items)
  before inserting any of the given items.
  So if a :class:`ValueNotUniqueError <bidict.ValueNotUniqueError>`
  is raised by an :func:`update() <bidict.bidict.update>` call,
  you can now be sure that none of the given items were inserted.

  Previously, any of the given items that were processed
  before the one causing the failure would have been inserted,
  and there was no good way to recover which were inserted
  and which had yet to be inserted at the time of the error,
  nor to undo the partial insertion after finding out
  not all items could be inserted.
  The new behavior makes it easier to reason about and control
  the effects of bulk insert operations.
  This is known as default ``precheck=True`` behavior.

  Because this improvement does require extra processing,
  you can opt out of it if you don't need it by calling
  :func:`putall() <bidict.bidict.putall>` with ``precheck=False``.

  Note: :class:`loosebidict.update() <bidict.loosebidict.update>`
  still defaults to ``precheck=False`` behavior.

- New exceptions, reflecting new cases where they're raised:

  - :class:`KeyNotUniqueError <bidict.KeyNotUniqueError>`
  - :class:`ValueNotUniqueError <bidict.ValueNotUniqueError>`
  - :class:`KeyAndValueNotUniqueError <bidict.KeyAndValueNotUniqueError>`
  - :class:`UniquenessError <bidict.UniquenessError>` (base class for the above)

- Add

  - :func:`bidict.compat.viewkeys`
  - :func:`bidict.compat.viewvalues`
  - :func:`bidict.compat.iterkeys`
  - :func:`bidict.compat.itervalues`
  - :func:`bidict.compat.izip`
  - :func:`bidict.compat.izip_longest`

  to complement the existing
  :func:`iteritems() <bidict.compat.iteritems>` and
  :func:`viewitems() <bidict.compat.viewitems>`
  compatibility helpers.

- Implement several functions more efficiently
  (including
  :func:`pairs() <bidict.util.pairs>`,
  :func:`inverted() <bidict.util.inverted>`, and
  :func:`bidict.copy() <bidict.BidirectionalMapping.copy>`).

- Implement :func:`bidict.BidirectionalMapping.__copy__`
  for use with the :mod:`copy` module.

- Fix issue preventing a client class from inheriting from
  :class:`loosebidict <bidict.loosebidict>`
  (see `#34 <https://github.com/jab/bidict/issues/34>`_).

- Add benchmarking to tests.

- Drop official support for CPython 3.3
  (it will probably continue to work but is no longer being tested).

Breaking API Changes
^^^^^^^^^^^^^^^^^^^^

- Rename ``KeyExistsException`` :class:`KeyNotUniqueError <bidict.KeyNotUniqueError>`
  and ``ValueExistsException`` :class:`ValueNotUniqueError <bidict.ValueNotUniqueError>`.


0.11.0 (2016-02-05)
-------------------

- Add
  :class:`bidict.orderedbidict`, 
  :class:`bidict.looseorderedbidict`,
  and
  :class:`bidict.frozenorderedbidict`.

- Adopt `Open Code of Conduct
  <http://todogroup.org/opencodeofconduct/#bidict/jab@math.brown.edu>`_.

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

- New :attr:`forceupdate() <bidict.bidict.forceupdate>` method
  provides a bulk :attr:`forceput() <bidict.bidict.forceput>` operation.

- Fix bugs in
  :attr:`pop() <bidict.bidict.pop>` and
  :attr:`setdefault() <bidict.bidict.setdefault>`
  which could leave a bidict in an inconsistent state.

Breaking API Changes
^^^^^^^^^^^^^^^^^^^^

- Remove ``bidict.__invert__``, and with it, support for the ``~b`` syntax.
  Use :attr:`b.inv <bidict.BidirectionalMapping.inv>` instead.
  `#19 <https://github.com/jab/bidict/issues/19>`_

- Remove support for the slice syntax.
  Use ``b.inv[val]`` rather than ``b[:val]``.
  `#19 <https://github.com/jab/bidict/issues/19>`_

- Remove ``bidict.invert``.
  Use :attr:`b.inv <bidict.BidirectionalMapping.inv>`
  rather than inverting a bidict in place.
  `#20 <https://github.com/jab/bidict/issues/20>`_

- Raise :class:`ValueExistsException <bidict.ValueExistsException>`
  when attempting to insert a mapping with a non-unique key.
  `#21 <https://github.com/jab/bidict/issues/21>`_

- Rename ``collapsingbidict`` to :class:`loosebidict <bidict.loosebidict>`
  now that it suppresses
  :class:`ValueExistsException <bidict.ValueExistsException>`
  rather than the less general ``CollapseException``.
  `#21 <https://github.com/jab/bidict/issues/21>`_

- ``CollapseException`` has been subsumed by
  :class:`ValueExistsException <bidict.ValueExistsException>`.
  `#21 <https://github.com/jab/bidict/issues/21>`_

- :attr:`put <bidict.bidict.put>` now raises :class:`KeyExistsException
  <bidict.KeyExistsException>` when attempting to insert an already-existing
  key, and :class:`ValueExistsException <bidict.ValueExistsException>` when
  attempting to insert an already-existing value.


0.9.0.post1 (2015-06-06)
------------------------

- Fix metadata missing in the 0.9.0rc0 release.


0.9.0rc0 (2015-05-30)
---------------------

- Add a Changelog!
  Also a
  `Contributors' Guide <https://github.com/jab/bidict/blob/master/CONTRIBUTING.rst>`_,
  `Gitter chat room <https://gitter.im/jab/bidict>`_,
  and other community-oriented improvements.

- Adopt Pytest (thanks Tom Viner and Adopt Pytest Month).

- Added property-based tests via
  `hypothesis <https://hypothesis.readthedocs.io>`_.

- Other code, tests, and docs improvements.

Breaking API Changes
^^^^^^^^^^^^^^^^^^^^

- Move :func:`bidict.iteritems` and :func:`bidict.viewitems`
  to new :attr:`bidict.compat` module.

- Move :class:`bidict.inverted`
  to new :attr:`bidict.util` module
  (still available from top-level :mod:`bidict` module as well).

- Move ``bidict.fancy_iteritems``
  to :func:`bidict.util.pairs`
  (also available from top level as :func:`bidict.pairs`).

- Rename ``bidict_type`` keyword arg to ``base_type``
  in :func:`bidict.namedbidict`.

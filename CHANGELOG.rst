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

  ``on_dup_kv`` can also take :attr:`bidict.DuplicationBehavior.ON_DUP_VAL`.

  If not provided,
  :func:`put() <bidict.bidict.put>` uses
  :attr:`RAISE <bidict.DuplicationBehavior.RAISE>` behavior default.

- New :func:`putall() <bidict.bidict.putall>` method
  provides a bulk :func:`put() <bidict.bidict.put>` API.

- :func:`bidict.update() <bidict.bidict.update>` now offers stronger
  consistency guarantees by checking for and handling duplication
  before inserting any of the given items.
  So if an :func:`update() <bidict.bidict.update>` call causes a
  :class:`ValueDuplicationError <bidict.ValueDuplicationError>`,
  you can now be sure that none of the given items were inserted.

  Previously, any of the given items that were processed
  before the one causing the failure would have been inserted,
  and there was no good way to recover which were inserted
  and which had yet to be inserted at the time of the error,
  nor to undo the partial insertion after finding out
  not all items could be inserted.
  The new behavior makes it easier to reason about and control
  the effects of bulk insert operations.
  This is known as "fail clean" behavior.

  The new :func:`putall() <bidict.bidict.putall>` method also fails clean.

- New exceptions:

  - :class:`KeyDuplicationError <bidict.KeyDuplicationError>`
  - :class:`ValueDuplicationError <bidict.ValueDuplicationError>`
  - :class:`KeyAndValueDuplicationError <bidict.KeyAndValueDuplicationError>`
  - :class:`DuplicationError <bidict.DuplicationError>` (base class for the above)

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

- When overwriting the key of an existing value in an
  :class:`bidict.orderedbidict`, the position of the existing item is
  now preserved rather than being moved to the end, which matches the
  behavior of preserving order when overwriting the value of an existing key.

- :func:`orderedbidict.move_to_end <bidict.orderedbidict.move_to_end>`
  now works on Python < 3.2.

- Fix issue preventing a client class from inheriting from
  :class:`loosebidict <bidict.loosebidict>`
  (see `#34 <https://github.com/jab/bidict/issues/34>`_).

- Add benchmarking to tests.

- Drop official support for CPython 3.3.
  (It may continue to work, but is no longer being tested.)

Breaking API Changes
^^^^^^^^^^^^^^^^^^^^

- Rename ``KeyExistsException`` :class:`KeyDuplicationError <bidict.KeyDuplicationError>`
  and ``ValueExistsException`` :class:`ValueDuplicationError <bidict.ValueDuplicationError>`.


0.11.0 (2016-02-05)
-------------------

- Add
  :class:`bidict.orderedbidict`, 
  :class:`bidict.looseorderedbidict`,
  and
  :class:`bidict.frozenorderedbidict`.

- Add :doc:`Code of Conduct <code-of-conduct>`
  (*GitHub link:* `<CODE_OF_CONDUCT.rst>`_).

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

- Raise ``ValueExistsException``
  when attempting to insert a mapping with a non-unique key.
  `#21 <https://github.com/jab/bidict/issues/21>`_

- Rename ``collapsingbidict`` to :class:`loosebidict <bidict.loosebidict>`
  now that it suppresses
  ``ValueExistsException``
  rather than the less general ``CollapseException``.
  `#21 <https://github.com/jab/bidict/issues/21>`_

- ``CollapseException`` has been subsumed by
  ``ValueExistsException``.
  `#21 <https://github.com/jab/bidict/issues/21>`_

- :attr:`put <bidict.bidict.put>` now raises ``KeyExistsException``
  when attempting to insert an already-existing
  key, and ``ValueExistsException`` when
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

- Move ``bidict.iteritems`` and ``bidict.viewitems``
  to new :mod:`bidict.compat` module.

- Move :class:`bidict.inverted`
  to new :attr:`bidict.util` module
  (still available from top-level :mod:`bidict` module as well).

- Move ``bidict.fancy_iteritems``
  to :func:`bidict.util.pairs`
  (also available from top level as :func:`bidict.pairs`).

- Rename ``bidict_type`` keyword arg to ``base_type``
  in :func:`bidict.namedbidict`.

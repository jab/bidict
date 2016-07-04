.. _changelog:

Changelog
=========

Release Notifications
---------------------

`Follow bidict on VersionEye <https://www.versioneye.com/python/bidict>`_
to automatically be notified via email
when a new version of bidict is released.

0.12.0 (2016-07-03)
-------------------

- New/renamed exceptions:

  - :class:`KeyDuplicationError <bidict.KeyDuplicationError>`
  - :class:`ValueDuplicationError <bidict.ValueDuplicationError>`
  - :class:`KeyAndValueDuplicationError <bidict.KeyAndValueDuplicationError>`
  - :class:`DuplicationError <bidict.DuplicationError>` (base class for the above)

- :func:`put() <bidict.bidict.put>`
  now accepts ``on_dup_key``, ``on_dup_val``, and ``on_dup_kv`` keyword args
  which allow you to override the default behavior
  when the key or value of a given item
  duplicates that (those) of any existing item(s).
  These can take the following values:

  - :attr:`bidict.DuplicationBehavior.RAISE`
  - :attr:`bidict.DuplicationBehavior.OVERWRITE`
  - :attr:`bidict.DuplicationBehavior.IGNORE`

  ``on_dup_kv`` can also take :attr:`bidict.DuplicationBehavior.ON_DUP_VAL`.

  If not provided,
  :func:`put() <bidict.bidict.put>` uses
  :attr:`RAISE <bidict.DuplicationBehavior.RAISE>` behavior by default.

- New :func:`putall() <bidict.bidict.putall>` method
  provides a bulk :func:`put() <bidict.bidict.put>` API,
  allowing you to override the default duplication handling behavior
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
  This required reimplementing :class:`orderedbidict <bidict.orderedbidict>`
  on top of two dicts and a linked list, rather than two OrderedDicts,
  since :class:`OrderedDict <collections.OrderedDict>` does not expose
  its underlying linked list.

- :func:`orderedbidict.move_to_end() <bidict.orderedbidict.move_to_end>`
  now works on Python < 3.2 as a result of the new
  :class:`orderedbidict <bidict.orderedbidict>` implementation.

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

- More efficient implementations of
  :func:`pairs() <bidict.util.pairs>`,
  :func:`inverted() <bidict.util.inverted>`, and
  :func:`bidict.copy() <bidict.BidirectionalMapping.copy>`.

- Implement :func:`bidict.__copy__() <bidict.BidirectionalMapping.__copy__>`
  for use with the :mod:`copy` module.

- Fix issue preventing a client class from inheriting from
  :class:`loosebidict <bidict.loosebidict>`
  (see `#34 <https://github.com/jab/bidict/issues/34>`_).

- Add benchmarking to tests.

- Drop official support for CPython 3.3.
  (It may continue to work, but is no longer being tested.)

Breaking API Changes
^^^^^^^^^^^^^^^^^^^^

- Rename ``KeyExistsException`` to :class:`KeyDuplicationError <bidict.KeyDuplicationError>`
  and ``ValueExistsException`` to :class:`ValueDuplicationError <bidict.ValueDuplicationError>`.

- When overwriting the key of an existing value in an :class:`orderedbidict <bidict.orderedbidict>`,
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

      >>> from bidict import orderedbidict
      >>> o = orderedbidict([(0, 1), (2, 3)])
      >>> o.forceput(4, 1)

  previously would have resulted in::

      >>> o  # doctest: +SKIP
      orderedbidict([(2, 3), (4, 1)])

  but now results in::

      >>> o
      orderedbidict([(4, 1), (2, 3)])


0.11.0 (2016-02-05)
-------------------

- Add
  :class:`bidict.orderedbidict`, 
  :class:`bidict.looseorderedbidict`,
  and
  :class:`bidict.frozenorderedbidict`.

- Add :doc:`Code of Conduct <code-of-conduct>`
  (`<./CODE_OF_CONDUCT.rst>`_ |
  `<https://bidict.readthedocs.io/code-of-conduct.html>`_).

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

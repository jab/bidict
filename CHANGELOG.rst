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

- Add benchmarking to tests,
  and implement several functions more efficiently
  (including
  :func:`pairs() <bidict.util.pairs>`,
  :func:`inverted() <bidict.util.inverted>`, and
  :func:`bidict.copy() <bidict.BidirectionalMapping.copy>`).
- :func:`put() <bidict.bidict.put>`
  now accepts ``on_dup_key`` and ``on_dup_val`` keyword arguments
  which allow you to override the default behavior
  when the key or value of a new item duplicates that of an existing one.
  These can take the following values:

  - :attr:`bidict.DuplicationBehavior.RAISE`
  - :attr:`bidict.DuplicationBehavior.OVERWRITE`
  - :attr:`bidict.DuplicationBehavior.IGNORE`

  For a :class:`bidict <bidict.bidict>`,
  ``on_dup_key`` defaults to
  :attr:`OVERWRITE <bidict.DuplicationBehavior.OVERWRITE>` and
  ``on_dup_val`` defaults to
  :attr:`RAISE <bidict.DuplicationBehavior.RAISE>`,
  while for a :class:`loosebidict <bidict.loosebidict>`
  both default to :attr:`OVERWRITE <bidict.DuplicationBehavior.OVERWRITE>`,
  maintaining backwards compatibility with the previous behavior
  when called with no keyword arguments.
- New :func:`putall() <bidict.bidict.putall>` method
  provides a bulk :func:`put() <bidict.bidict.put>` API.
- Make initialization and bulk insert operations safer and more predictable
  by checking for and processing items with duplicate keys and values
  ahead of inserting any of the given items, by default.
  So e.g. if a :class:`ValueExistsError <bidict.ValueExistsError>`
  is raised by an :func:`update() <bidict.bidict.update>` call,
  you can be sure that none of the given items were inserted.
  This default behavior can be overridden when calling
  :func:`putall() <bidict.bidict.putall>` by passing *atomic=False*.
- New exceptions provide more precise information about error conditions:

  - :class:`UniquenessError <bidict.UniquenessError>`
  - :class:`KeyNotUniqueError <bidict.KeyNotUniqueError>`
  - :class:`ValueNotUniqueError <bidict.ValueNotUniqueError>`
- Drop official support for CPython 3.3
  (it will probably continue to work but is no longer being tested).
- Fix issue preventing a client class from inheriting from
  :class:`loosebidict <bidict.loosebidict>`
  (see `#34 <https://github.com/jab/bidict/issues/34>`_)
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
- Implement :func:`bidict.BidirectionalMapping.__copy__`
  for use with the :mod:`copy` module.

Breaking API Changes
^^^^^^^^^^^^^^^^^^^^

- Rename ``KeyExistsException`` :class:`KeyExistsError <bidict.KeyExistsError>`
  and ``ValueExistsException`` :class:`ValueExistsError <bidict.ValueExistsError>`.


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

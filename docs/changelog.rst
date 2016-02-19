.. _changelog:

Changelog
=========

0.12.0-dev (not yet released)
-----------------------------

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
- Add benchmarking to tests.
- :attr:`put() <bidict.bidict.put>`
  now accepts ``key_clbhv`` and ``val_clbhv`` keyword arguments
  which allow you to override the default behavior
  when the key or value of a new item collides with that of an existing one.
  These can take the following values:

  - :attr:`bidict.CollisionBehavior.RAISE`
  - :attr:`bidict.CollisionBehavior.OVERWRITE`
  - :attr:`bidict.CollisionBehavior.IGNORE`

  For a :class:`bidict <bidict.bidict>`,
  ``key_clbhv`` defaults to
  :attr:`OVERWRITE <bidict.CollisionBehavior.OVERWRITE>` and
  ``val_clbhv`` defaults to
  :attr:`RAISE <bidict.CollisionBehavior.RAISE>`,
  while for a :class:`loosebidict <bidict.loosebidict>`
  both default to :attr:`OVERWRITE <bidict.CollisionBehavior.OVERWRITE>`,
  maintaining backwards compatibility with the previous behavior
  when called with no keyword arguments.
- New :func:`putall() <bidict.bidict.putall>` method
  provides a bulk :attr:`put() <bidict.bidict.put>` API.
- Make bulk insert operations (including initialization) safer
  by not allowing any inserts to succeed if any one would cause
  an exception to be raised.
- Improve performance of bulk insert operations (including initialization)
  by at least 2-3x in common cases.
- New exceptions provide more specificity
  in various exceptional cases:

  - :class:`UniquenessException <bidict.UniquenessException>`
  - :class:`NonuniqueKeysException <bidict.NonuniqueKeysException>`
  - :class:`NonuniqueValuesException <bidict.NonuniqueValuesException>`
  - :class:`KeysExistException <bidict.KeysExistException>`
  - :class:`ValuesExistException <bidict.ValuesExistException>`
- Drop official support for CPython 3.3
  (it will probably continue to work but is no longer being tested).

0.11.0 (2016-02-05)
-------------------

- Add
  :class:`bidict.orderedbidict`, 
  :class:`bidict.looseorderedbidict`,
  and
  :class:`bidict.frozenorderedbidict`.
- Adopt `Open Code of Conduct
  <http://todogroup.org/opencodeofconduct/#bidict/jab@math.brown.edu>`_.
- Drop official support for pypy3
  (it still may work but is no longer being tested).
  bidict may add back support for pypy3 once it's made more progress.

0.10.0.post1 (2015-12-23)
-------------------------

- Minor documentation fixes/improvements


0.10.0 (2015-12-23)
-------------------

- Removed several features in favor of keeping the API simpler
  and the code more maintainable.
- In the interest of protecting data safety more proactively, by default
  bidict now raises an error on attempting to insert a non-unique value,
  rather than allowing its associated key to be silently overwritten.
  See discussion in `#21 <https://github.com/jab/bidict/issues/21>`_.
- New :attr:`forceupdate() <bidict.bidict.forceupdate>` method
  for bulk :attr:`forceput() <bidict.bidict.forceput>`.
- Fix bugs in
  :attr:`pop() <bidict.bidict.pop>` and
  :attr:`setdefault() <bidict.bidict.setdefault>`
  which could leave a bidict in an inconsistent state.

Breaking API Changes
^^^^^^^^^^^^^^^^^^^^

- Removed ``bidict.__invert__``, and with it, support for the ``~b`` syntax.
  Use :attr:`b.inv <bidict.BidirectionalMapping.inv>` instead.
  `#19 <https://github.com/jab/bidict/issues/19>`_
- Removed support for the slice syntax.
  Use ``b.inv[val]`` rather than ``b[:val]``.
  `#19 <https://github.com/jab/bidict/issues/19>`_
- Removed ``bidict.invert``.
  Use :attr:`b.inv <bidict.BidirectionalMapping.inv>`
  rather than inverting a bidict in place.
  `#20 <https://github.com/jab/bidict/issues/20>`_
- Raise :class:`ValueExistsException <bidict.ValueExistsException>`
  when attempting to insert a mapping with a non-unique key.
  `#21 <https://github.com/jab/bidict/issues/21>`_
- Renamed ``collapsingbidict`` to :class:`loosebidict <bidict.loosebidict>`
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

- Fixed metadata missing in the 0.9.0rc0 release


0.9.0rc0 (2015-05-30)
---------------------

- Added a Changelog!
  Also a
  `Contributors' Guide <https://github.com/jab/bidict/blob/master/CONTRIBUTING.rst>`_,
  `Gitter chat room <https://gitter.im/jab/bidict>`_,
  and other community-oriented improvements
- Adopted Pytest (thanks Tom Viner and Adopt Pytest Month)
- Added property-based tests via
  `hypothesis <https://hypothesis.readthedocs.org>`_
- Other code, tests, and docs improvements

Breaking API Changes
^^^^^^^^^^^^^^^^^^^^

- Moved :func:`bidict.iteritems` and :func:`bidict.viewitems`
  to new :attr:`bidict.compat` module
- Moved :class:`bidict.inverted`
  to new :attr:`bidict.util` module
  (still available from top-level :mod:`bidict` module as well)
- Moved/renamed ``bidict.fancy_iteritems``
  to :func:`bidict.util.pairs`
  (also available from top level as :func:`bidict.pairs`)
- Renamed ``bidict_type`` keyword arg to ``base_type``
  in :func:`bidict.namedbidict`

.. _changelog:

Changelog
=========

0.10.0 (not yet released)
-------------------------

- Removed several features in favor of keeping the API simpler
  and the code more maintainable.
- In the interest of protecting data safety more proactively, by default
  bidict now raises an error on attempting to insert a non-unique value,
  rather than allowing its associated key to be silently overwritten.
  See discussion in `#21 <https://github.com/jab/bidict/issues/21>`_.
- New :attr:`forceupdate <bidict.bidict.forceupdate>` method
  for bulk :attr:`forceput <bidict.bidict.forceput>`.

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

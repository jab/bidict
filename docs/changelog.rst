.. _changelog:

Changelog
=========

0.10.0 (not yet released)
-------------------------

- Removed several features in favor of keeping the API simpler
  and the code more maintainable
- Stricter one-to-one checking checking by default
- New :attr:`bidict.bidict.forceupdate`` method for bulk forceput

Breaking API Changes
^^^^^^^^^^^^^^^^^^^^

- Removed ``bidict.__invert__``, and with it, support for the ``~b`` syntax.
  Use ``b.inv`` instead.
  `#19 <https://github.com/jab/bidict/issues/19>`_
- Removed support for the slice syntax.
  Use ``b.inv[val]`` rather than ``b[:val]``.
  `#19 <https://github.com/jab/bidict/issues/19>`_
- Removed ``bidict.invert``.
  Use ``b.inv`` rather than inverting a bidict in place.
  `#20 <https://github.com/jab/bidict/issues/20>`_
- Raise :class:`bidict.ValueExistsException`` when attempting to insert a new
  key associated with an existing value
- Rename ``collapsingbidict`` to :class:`bidict.loosebidict`` now that it's
  loose in the case of :class:`bidict.ValueExistsException`` too


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

.. _changelog:

Changelog
=========

0.9.0-dev (not yet released)
----------------------------

- Adopt Pytest (thanks Tom Viner and Adopt Pytest Month)
- Add property-based tests via `hypothesis <https://hypothesis.readthedocs.org>`_
- Make code and docs more modular
- Project layout improvements to support the above
- Partial support for slices like ``b[:None]``
  (see `caveat <https://bidict.readthedocs.org/en/master/caveats.html#none-breaks-the-slice-syntax>`_)

API
^^^

- moved :func:`bidict.iteritems` and :func:`bidict.viewitems`
  to new :attr:`bidict.compat` module
- moved :class:`bidict.inverted`
  to new :attr:`bidict.util` module
  (still available from top-level :mod:`bidict` module as well)
- moved/renamed ``bidict.fancy_iteritems``
  to :func:`bidict.util.pairs`
  (also available from top level as :func:`bidict.pairs`)
- renamed ``bidict_type`` keyword arg to ``base_type``
  in :func:`bidict.namedbidict`

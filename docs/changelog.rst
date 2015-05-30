.. _changelog:

Changelog
=========

0.9.0rc0 (2015-05-30)
----------------------------

- Add a Changelog!
  Also a
  `Contributors' Guide <https://github.com/jab/bidict/blob/master/CONTRIBUTING.rst>`_,
  `Gitter chat room <https://gitter.im/jab/bidict>`_,
  and other community-oriented improvements
- Adopt Pytest (thanks Tom Viner and Adopt Pytest Month)
- Add property-based tests via `hypothesis <https://hypothesis.readthedocs.org>`_
- Other code, tests, and docs improvements

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

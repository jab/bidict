Learning from bidict
--------------------

I have learned a surprisingly large amount
of fascinating advanced Python programming
in the process of developing bidict,
especially in light of its relatively small codebase.

Below are some of the fun Python corners I got to explore further
thanks to working on bidict.
If you are interested in learning more about any of the following,
reading and contributing to bidict's code
could be a great way to do so.

TODO: Expand all of the following, and
include more specific references to bidict's usages.


API Design
==========

- Making APIs "Pythonic"

  - `Zen of Python <https://www.python.org/dev/peps/pep-0020/#id3>`_

  - "Errors should never pass silently.
    Unless explicitly silenced.
    In the face of ambiguity, refuse the temptation to guess."
    → bidict's default duplication policies

  - "Explicit is better than implicit.
    There should be one—and preferably only one—obvious way to do it."
    → dropped the alternate ``.inv`` APIs that used
    the ``~`` operator and the slice syntax hack

- Integrating with :mod:`collections` via :mod:`collections.abc` and :mod:`abc`

  - Extending :class:`collections.abc.Mapping` and :class:`collections.abc.MutableMapping`

  - Using :meth:`abc.ABCMeta.register`,
    :meth:`abc.ABCMeta.__subclasshook__`, and
    :obj:`NotImplemented`.

- Beyond :class:`collections.abc.Mapping`, bidicts implement as much of the
  :class:`dict` and :class:`~collections.OrderedDict` APIs as possible.
  When working with APIs, familiarity and memorability are hugely important.


Python's data model
===================

- Making an immutable type hashable, i.e. insertable into :class:`dict`\s and :class:`set`\s
  (see :meth:`object.__hash__` and :meth:`object.__eq__`),
  how that interacts with ordered vs. unordered hashable types
  that may compare equal
  (e.g.
  :class:`~bidict.frozenbidict` and
  :class:`~bidict.FrozenOrderedBidict`),
  some interesting resulting corner cases

  - :ref:`nan-as-key`

  - equal keys of different type,
    intransitive equality (as in :class:`~collections.OrderedDict`):
    https://github.com/cosmologicon/pywat/issues/38

    - "Intransitive equality was a mistake." –Raymond Hettinger

- Using :meth:`object.__new__` to bypass default object initialization

- Using :meth:`object.__reduce__` to make an object pickleable that otherwise wouldn't be,
  due to e.g. using weakrefs (see below)

- Overriding :meth:`object.__getattribute__` for custom attribute lookup
  (see :ref:`sorted-bidict-recipes` for example)


Implementing an ordered mapping using a circular doubly-linked list
===================================================================

OrderedDict's
`implementation <https://github.com/python/cpython/blob/a0374d/Lib/collections/__init__.py#L71>`_
is a great reference.


Portability
===========

- Python 2 vs. Python 3 (:class:`dict` API changes)

- CPython vs. PyPy

  - gc / weakref differences


Correctness, performance, code quality, etc.
============================================

bidict provided a need to learn these fantastic tools,
many of which have been indispensable:

-  `Pytest <https://docs.pytest.org/en/latest/>`_
-  `Coverage <http://coverage.readthedocs.io/en/latest/>`_
-  `hypothesis <http://hypothesis.readthedocs.io/en/latest/>`_
-  `pytest-benchmark <https://github.com/ionelmc/pytest-benchmark>`_
-  `Sphinx <http://www.sphinx-doc.org/en/stable/>`_
-  `Travis <https://travis-ci.org/>`_
-  `Readthedocs <http://bidict.readthedocs.io/en/latest/>`_
-  `Codecov <https://codecov.io>`_
-  `lgtm <http://lgtm.com/>`_
-  `Pylint <https://www.pylint.org/>`_
-  `setuptools_scm <https://github.com/pypa/setuptools_scm>`_

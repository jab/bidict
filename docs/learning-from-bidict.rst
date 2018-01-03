Learning from bidict
--------------------

Below are some of the more fascinating Python corners
I got to explore further
thanks to working on bidict.

If you are interested in learning more about any of the following,
reading through or even contributing to bidict's code
could be a great way to get started.

.. todo::

   The following is just an outline.
   Expand and provide more references and examples.


Python's data model
===================

- Making an immutable type hashable,
  i.e. insertable into :class:`dict`\s and :class:`set`\s

  - See :meth:`object.__hash__` and :meth:`object.__eq__` docs

  - How this affects hashable ordered collections
    like :class:`~bidict.FrozenOrderedBidict`
    that have an order-insensitive
    :meth:`~bidict.FrozenOrderedBidict.__eq__`

    - All contained items must participate in the hash

- Resulting corner cases produce possibly surprising results:

  - See :ref:`nan-as-key`

  - See
    `pywat#38 <https://github.com/cosmologicon/pywat/issues/38>`_
    for some surprising results when keys of different types compare equal,
    or when a hashable type's ``__eq__()`` is intransitive
    (as in :class:`~collections.OrderedDict`):

    - "Intransitive equality was a mistake." –Raymond Hettinger

    - Thus :ref:`eq-order-insensitive` for :class:`~bidict.FrozenOrderedBidict`

- Using :meth:`object.__new__` to bypass default object initialization,
  e.g. for better :meth:`~bidict.bidict.copy` performance

  - See `how bidict does this
    <https://github.com/jab/bidict/blob/master/bidict/_frozen.py>`_

- Overriding :meth:`object.__getattribute__` for custom attribute lookup

  - See :ref:`sorted-bidict-recipes` for example

- Using :meth:`object.__reduce__` to make an object pickleable
  that otherwise wouldn't be,
  due to e.g. using weakrefs (see below)


Using :mod:`weakref`
====================

- See :ref:`inv-avoids-reference-cycles`


:func:`~collections.namedtuple`-style dynamic class generation
==============================================================

- See `namedbidict's implementation
  <https://github.com/jab/bidict/blob/master/bidict/_named.py>`_


How to efficiently implement an ordered mapping
===============================================

- Use a backing dict and doubly-linked list
  `like OrderedDict
  <https://github.com/python/cpython/blob/a0374d/Lib/collections/__init__.py#L71>`_

- See `OrderedBidict's implementation
  <https://github.com/jab/bidict/blob/master/bidict/_ordered.py>`_


API Design
==========

- Integrating with :mod:`collections` via :mod:`collections.abc` and :mod:`abc`

  - Extending :class:`collections.abc.Mapping` and :class:`collections.abc.MutableMapping`

  - How to make virtual subclasses using
    :meth:`abc.ABCMeta.register` or
    :meth:`abc.ABCMeta.__subclasshook__` and
    :obj:`NotImplemented`.

- Beyond :class:`collections.abc.Mapping`, bidicts implement additional APIs
  that :class:`dict` and :class:`~collections.OrderedDict` implement.

  - When creating a new API, making it familiar, memorable, and intuitive
    is hugely important to a good user experience.

- Making APIs Pythonic

  - `Zen of Python <https://www.python.org/dev/peps/pep-0020/>`_

  - "Errors should never pass silently.
    Unless explicitly silenced.
    In the face of ambiguity, refuse the temptation to guess."
    → bidict's default duplication policies

  - "Explicit is better than implicit.
    There should be one—and preferably only one—obvious way to do it."
    → dropped the alternate ``.inv`` APIs that used
    the ``~`` operator and the old slice syntax


Portability
===========

- Python 2 vs. Python 3 (mostly :class:`dict` API changes)

- CPython vs. PyPy

  - gc / weakref

    - http://doc.pypy.org/en/latest/cpython_differences.html#differences-related-to-garbage-collection-strategies
    - hence https://github.com/jab/bidict/blob/958ca85/tests/test_hypothesis.py#L168

  - nan


Correctness, performance, code quality, etc.
============================================

bidict provided a need to learn these fantastic tools,
many of which have been indispensable
(especially hypothesis – see
`bidict's usage <https://github.com/jab/bidict/blob/master/tests/test_hypothesis.py>`_):

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

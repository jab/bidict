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

- Using :meth:`object.__new__` to bypass default object initialization,
  e.g. for better :meth:`~bidict.bidict.copy` performance

  - See `how bidict does this
    <https://github.com/jab/bidict/blob/958ca85/bidict/_frozen.py>`_

- Overriding :meth:`object.__getattribute__` for custom attribute lookup

  - See :ref:`sorted-bidict-recipes` for example

- Using :meth:`object.__reduce__` to make an object pickleable
  that otherwise wouldn't be,
  due to e.g. using weakrefs (see below)

- Making an immutable type hashable,
  i.e. insertable into :class:`dict`\s and :class:`set`\s

  - See :meth:`object.__hash__` and :meth:`object.__eq__` docs

  - If overriding :meth:`object.__eq__`, don't forget to override
    :meth:`object.__ne__`

  - How this affects hashable ordered collections
    like :class:`~bidict.FrozenOrderedBidict`
    that have an order-insensitive
    :meth:`~bidict.FrozenOrderedBidict.__eq__`

    - All contained items must participate in the hash,
      order-insensitively

    - The `collections.abc.Set._hash <https://github.com/python/cpython/blob/a0374d/Lib/_collections_abc.py#L521>`_
      method provides a pure Python implementation of the same hash algorithm
      used to hash :class:`frozenset`\s.

      Since :class:`~collections.abc.ItemsView` extends
      :class:`~collections.abc.Set`, :class:`~bidict.frozenbidict`
      can just call ``ItemsView(self)._hash()``.

        - Why is :meth:`collections.abc.Set._hash` private?

        - Why isn't the C implementation of this algorithm directly exposed in
          CPython? Only way to use it is to call ``hash(frozenset(self.items()))``,
          which wastes memory allocating the ephemeral frozenset,
          and time copying all the items into it before they're hashed.

- Resulting corner cases produce possibly surprising results:

  - See :ref:`nan-as-key`

  - See
    `pywat#38 <https://github.com/cosmologicon/pywat/issues/38>`_
    for some surprising results when keys of
    (related but) different types compare equal,
    or when a hashable type's ``__eq__()`` is intransitive
    (as in :class:`~collections.OrderedDict`):

    - "Intransitive equality was a mistake." –Raymond Hettinger

    - Thus :ref:`eq-order-insensitive` for ordered bidicts

  - If a :class:`~bidict.bidict` contains the same items as another
    :class:`~collections.abc.Mapping` of a different subtype,
    should the :class:`~bidict.bidict` compare equal to the other mapping?
    Or should it at least compare unequal if the other instance is not
    also a :class:`~bidict.BidirectionalMapping`?
    Or should it return the :obj:`NotImplemented` object?

    - bidict's ``__eq__()`` design errs on the side of allowing more type polymorphism,
      on the grounds that this is probably what the majority of use cases expect and that this
      is more Pythonic.

    - Any user who does need exact-type-matching equality can just override
      :meth:`bidict’s __eq__() <bidict.frozenbidict.__eq__>` method in a subclass.

      - If this subclass were also hashable, would it be worth overriding
        :meth:`bidict.frozenbidict.__hash__` too to include the type?

      - Only point would be to reduce collisions when multiple instances of different
        :class:`~bidict.frozenbidict` subclasses contained the same items
        and were going to be inserted into the same :class:`dict` or :class:`set`
        (since they'd now be unequal but would hash to the same value otherwise).
        Seems rare, probably not worth it.


Using :mod:`weakref`
====================

- See :ref:`inv-avoids-reference-cycles`


:func:`~collections.namedtuple`-style dynamic class generation
==============================================================

- See `namedbidict's implementation
  <https://github.com/jab/bidict/blob/958ca85/bidict/_named.py>`_


How to efficiently implement an ordered mapping
===============================================

- Use a backing dict and doubly-linked list. :class:`~collections.OrderedDict`
  `provides a good example
  <https://github.com/python/cpython/blob/a0374d/Lib/collections/__init__.py#L71>`_

- See `OrderedBidict's implementation
  <https://github.com/jab/bidict/blob/958ca85/bidict/_ordered.py>`_


API Design
==========

- Integrating with :mod:`collections` via :mod:`collections.abc` and :mod:`abc`

- Implementing ABCs like :class:`collections.abc.Hashable`

- Thanks to :class:`~collections.abc.Hashable`
  implementing :meth:`abc.ABCMeta.__subclasshook__`,
  implementing a class that implements all the required methods of the
  :class:`~collections.abc.Hashable` interface
  (that is, just :meth:`~collections.abc.Hashable.__hash__` in this case)
  makes it a virtual subclass already, no need to explicitly extend.
  I.e. As long as ``Foo`` implements a ``__hash__()`` method,
  ``issubclass(Foo, Hashable)`` would always be True,
  no need to explicitly subclass via ``class Foo(Hashable):``

- :class:`collections.abc.Mapping` and
  :class:`collections.abc.MutableMapping`
  don't implement :meth:`~abc.ABCMeta.__subclasshook__`,
  so must either explicitly subclass
  (if you want to inherit any of their implementations)
  or use :meth:`abc.ABCMeta.register`
  (to register as a virtual subclass without inheriting any implementation)

- Providing a new open ABC like :class:`~bidict.BidirectionalMapping`

  - Implement :meth:`abc.ABCMeta.__subclasshook__`

    - Can return the :obj:`NotImplemented` object

  - See `how bidict.BidirectionalMapping does this
    <https://github.com/jab/bidict/blob/958ca85/bidict/_abc.py>`_

- Notice we have :class:`collections.abc.Reversible`
  but no ``collections.abc.Ordered`` or ``collections.abc.OrderedMapping``

  - Would have been useful for bidict's ``__repr__()`` implementation
    (see `source <https://github.com/jab/bidict/blob/958ca85/bidict/_frozen.py#L165>`_),
    and potentially for interop with other ordered mapping implementations
    such as `SortedDict <http://www.grantjenks.com/docs/sortedcontainers/sorteddict.html>`_

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

  - primitives' identities, nan, etc.

    - http://doc.pypy.org/en/latest/cpython_differences.html#object-identity-of-primitive-values-is-and-id


Correctness, performance, code quality, etc.
============================================

bidict provided a need to learn these fantastic tools,
many of which have been indispensable
(especially hypothesis – see
`bidict's usage <https://github.com/jab/bidict/blob/958ca85/tests/test_hypothesis.py>`_):

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

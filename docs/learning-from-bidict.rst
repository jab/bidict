Learning from bidict
--------------------

Below is an outline of
some of the more fascinating Python corners
I got to explore further
thanks to working on bidict.

If you are interested in learning more about any of the following,
:ref:`reviewing the (small) codebase <home:Reviewers Wanted!>`
could be a great way to get started.


Python's data model
===================

- Using :meth:`object.__new__` to bypass default object initialization,
  e.g. for better :meth:`~bidict.bidict.copy` performance.
  See ``_base.py``.

- Overriding :meth:`object.__getattribute__` for custom attribute lookup.
  See :ref:`extending:Sorted Bidict Recipes`.

- Using
  :meth:`object.__getstate__`,
  :meth:`object.__setstate__`, and
  :meth:`object.__reduce__` to make an object pickleable
  that otherwise wouldn't be,
  due to e.g. using weakrefs,
  as bidicts do (covered further below).

- Using :ref:`slots` to speed up attribute access and reduce memory usage.
  Must be careful with pickling and weakrefs.
  See ``BidictBase.__getstate__()``.

- What happens when you implement a custom :meth:`~object.__eq__`?
  e.g. ``a == b`` vs. ``b == a`` when only ``a`` is an instance of your class?
  Great write-up in https://eev.ee/blog/2012/03/24/python-faq-equality/

- Making an immutable type hashable
  (so it can be inserted into :class:`dict`\s and :class:`set`\s):
  Must implement :meth:`~object.__hash__` such that
  ``a == b ⇒ hash(a) == hash(b)``.
  See the :meth:`object.__hash__` and :meth:`object.__eq__` docs.
  See :class:`bidict.frozenbidict`.

  - Consider :class:`~bidict.FrozenOrderedBidict`:
    its :meth:`~bidict.FrozenOrderedBidict.__eq__`
    is :ref:`order-insensitive <eq-order-insensitive>`.
    So all contained items must participate in the hash order-insensitively.

  - Can use `collections.abc.Set._hash <https://github.com/python/cpython/blob/a0374d/Lib/_collections_abc.py#L521>`__
    which provides a pure Python implementation of the same hash algorithm
    used to hash :class:`frozenset`\s.
    (Since :class:`~collections.abc.ItemsView` extends
    :class:`~collections.abc.Set`,
    :meth:`bidict.frozenbidict.__hash__`
    just calls ``ItemsView(self)._hash()``.)

    - Does this argue for making :meth:`collections.abc.Set._hash` non-private?

    - Why isn't the C implementation of this algorithm directly exposed in
      CPython? Only way to use it is to call ``hash(frozenset(self.items()))``,
      which wastes memory allocating the ephemeral frozenset,
      and time copying all the items into it before they're hashed.

  - Unlike other attributes, if a class implements ``__hash__()``,
    any subclasses of that class will not inherit it.
    It's like Python implicitly adds ``__hash__ = None`` to the body
    of every class that doesn't explicitly define ``__hash__``.
    So if you do want a subclass to inherit a base class's ``__hash__()``
    implementation, you have to set that manually,
    e.g. by adding ``__hash__ = BaseClass.__hash__`` in the class body.
    See :class:`~bidict.FrozenOrderedBidict`.

    This is consistent with the fact that
    :class:`object` implements ``__hash__()``,
    but subclasses of :class:`object`
    are not hashable by default.

- Surprising :class:`~collections.abc.Mapping` corner cases:

  - :ref:`addendum:nan as key`

  - :ref:`addendum:Equivalent but distinct \:class\:\`~collections.abc.Hashable\`\\s`

  - `pywat#38 <https://github.com/cosmologicon/pywat/issues/38>`__

    - "Intransitive equality
      (of :class:`~collections.OrderedDict`)
      was a mistake." –Raymond Hettinger

    - Hence :ref:`eq-order-insensitive`
      for ordered bidicts.

- If an instance of your custom mapping type
  contains the same items as a mapping of another type,
  should they compare equal?
  What if one of the mappings is ordered and the other isn't?
  What about returning the :obj:`NotImplemented` object?

  - bidict's ``__eq__()`` design
    errs on the side of allowing more type polymorphism
    on the grounds that this is what the majority of use cases expect,
    and that it's more Pythonic.

  - Any user who does need exact-type-matching equality can just override
    :meth:`bidict’s __eq__() <bidict.BidictBase.__eq__>` method in a subclass.

    - If this subclass were also hashable, would it be worth overriding
      :meth:`bidict.frozenbidict.__hash__` too to include the type?

    - Only point would be to reduce collisions when multiple instances of different
      types contained the same items
      and were going to be inserted into the same :class:`dict` or :class:`set`
      (since they'd now be unequal but would hash to the same value otherwise).
      Probably not worth it.


Using :mod:`weakref`
====================

See :ref:`addendum:\:attr\:\`~bidict.BidictBase.inv\` Avoids Reference Cycles`.


Other interesting stuff in the standard library
===============================================

- :mod:`reprlib` and :func:`reprlib.recursive_repr`
  (but not needed for bidict because there's no way to insert a bidict into itself)
- :func:`operator.methodcaller`
- :attr:`platform.python_implementation`
- See :ref:`addendum:Missing bidicts in Stdlib!`


Subclassing :func:`~collections.namedtuple` classes
===================================================

To get the performance benefits, intrinsic sortability, etc.
of :func:`~collections.namedtuple`
while customizing behavior, state, API, etc.,
you can subclass a :func:`~collections.namedtuple` class.
Just make sure to include ``__slots__ = ()``,
or you'll lose a lot of the performance benefits.

``_marker.py`` contains a small example.
Here's a larger one:

.. code:: python

   >>> from collections import namedtuple
   >>> from itertools import count

   >>> class Node(namedtuple('_Node', 'cost tiebreaker data parent')):
   ...     """Represent nodes in a graph traversal. Suitable for use with e.g. heapq."""
   ...
   ...     __slots__ = ()
   ...     _counter = count()  # break ties between equal-cost nodes, avoid comparing data
   ...
   ...     # Give call sites a cleaner API for creating new Nodes
   ...     def __new__(cls, cost, data, parent=None):
   ...         tiebreaker = next(cls._counter)
   ...         return super(Node, cls).__new__(cls, cost, tiebreaker, data, parent)
   ...
   ...     @property
   ...     def depth(self):
   ...         return self.parent.depth + 1 if self.parent else 0
   ...
   ...     def __repr__(self):
   ...         return 'Node(cost={cost}, data={data!r})'.format(**self._asdict())

   >>> start = Node(cost=0, data='foo')
   >>> child = Node(cost=5, data='bar', parent=start)
   >>> child
   Node(cost=5, data='bar')
   >>> child.parent
   Node(cost=0, data='foo')
   >>> child.depth
   1


:func:`~collections.namedtuple`-style dynamic class generation
==============================================================

See ``_named.py``.


How to efficiently implement an ordered mapping
===============================================

- Use a backing dict and doubly-linked list.

- See ``_orderedbase.py``.
  :class:`~collections.OrderedDict` provided a good
  `reference <https://github.com/python/cpython/blob/a0374d/Lib/collections/__init__.py#L71>`_.


API Design
==========

- Integrating with :mod:`collections` via :mod:`collections.abc` and :mod:`abc`

- Implementing ABCs like :class:`collections.abc.Hashable`

- Thanks to :class:`~collections.abc.Hashable`
  implementing :meth:`abc.ABCMeta.__subclasshook__`,
  any class that implements all the required methods of the
  :class:`~collections.abc.Hashable` interface
  (namely, :meth:`~collections.abc.Hashable.__hash__`)
  makes it a virtual subclass already, no need to explicitly extend.
  I.e. As long as ``Foo`` implements a ``__hash__()`` method,
  ``issubclass(Foo, Hashable)`` will always be True,
  no need to explicitly subclass via ``class Foo(Hashable): ...``

- :class:`collections.abc.Mapping` and
  :class:`collections.abc.MutableMapping`
  don't implement :meth:`~abc.ABCMeta.__subclasshook__`,
  so must either explicitly subclass
  (if you want to inherit any of their implementations)
  or use :meth:`abc.ABCMeta.register`
  (to register as a virtual subclass without inheriting any implementation)

- Providing a new open ABC like :class:`~bidict.BidirectionalMapping`

  - Just override :meth:`~abc.ABCMeta.__subclasshook__`.
    See ``_abc.py``.

  - Interesting consequence of the ``__subclasshook__()`` design:
    the "subclass" relation is now intransitive,
    e.g. :class:`object` is a subclass of :class:`~collections.abc.Hashable`,
    :class:`list` is a subclass of :class:`object`,
    but :class:`list` is not a subclass of :class:`~collections.abc.Hashable`

- Notice we have :class:`collections.abc.Reversible`
  but no ``collections.abc.Ordered`` or ``collections.abc.OrderedMapping``.
  Proposed in `bpo-28912 <https://bugs.python.org/issue28912>`__ but rejected.
  Would have been useful for bidict's ``__repr__()`` implementation (see ``_base.py``),
  and potentially for interop with other ordered mapping implementations
  such as `SortedDict <http://www.grantjenks.com/docs/sortedcontainers/sorteddict.html>`__

- Beyond :class:`collections.abc.Mapping`, bidicts implement additional APIs
  that :class:`dict` and :class:`~collections.OrderedDict` implement.

  - When creating a new API, making it familiar, memorable, and intuitive
    is hugely important to a good user experience.

- Making APIs Pythonic

  - `Zen of Python <https://www.python.org/dev/peps/pep-0020/>`__

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

- Python 2 vs. Python 3

  - mostly :class:`dict` API changes,
    but also functions like :func:`zip`, :func:`map`, :func:`filter`, etc.

  - If you define a custom :meth:`~object.__eq__` on a class,
    it will *not* be used for ``!=`` comparisons on Python 2 automatically;
    you must explicitly add an :meth:`~object.__ne__` implementation
    that calls your :meth:`~object.__eq__` implementation.
    If you don't, :meth:`object.__ne__` will be used instead,
    which behaves like ``is not``.
    GOTCHA alert!

    Python 3 thankfully fixes this.

  - borrowing methods from other classes:

    In Python 2, must grab the ``.im_func`` / ``__func__``
    attribute off the borrowed method to avoid getting
    ``TypeError: unbound method ...() must be called with ... instance as first argument``

    See ``_frozenordered.py``.

- CPython vs. PyPy

  - gc / weakref

    - http://doc.pypy.org/en/latest/cpython_differences.html#differences-related-to-garbage-collection-strategies
    - hence ``test_no_reference_cycles`` (in ``test_hypothesis.py``)
      is skipped on PyPy

  - primitives' identities, nan, etc.

    - http://doc.pypy.org/en/latest/cpython_differences.html#object-identity-of-primitive-values-is-and-id


Python Syntax hacks
===================

:class:`~bidict.bidict` used to support
`slice syntax <http://bidict.readthedocs.io/en/v0.9.0.post1/intro.html#bidict-bidict>`__
for looking up keys by value.

See `this <https://github.com/jab/bidict/blob/356dbe3/bidict/_bidict.py#L25>`__
for an example of how it was implemented.

See `#19 <https://github.com/jab/bidict/issues/19>`__ for why it was dropped.


Tools
=====

See :ref:`thanks:Projects` for some of the fantastic tools
for software verification, performance, code quality, etc.
that bidict has provided a reason to learn and master.

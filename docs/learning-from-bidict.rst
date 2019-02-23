Learning from bidict
--------------------

Below is an outline of
some of the more fascinating Python corners
I got to explore further
thanks to working on bidict.

If you are interested in learning more about any of the following,
I highly encourage you to
`read bidict's code <https://github.com/jab/bidict/blob/master/bidict/_abc.py#L10>`__.

I've sought to optimize the code not just for correctness and for performance,
but also to make it a pleasure to read,
to share the `joys of computing <https://joy.recurse.com/posts/148-bidict>`__
in bidict with others.

I hope it brings you some of the joy it's brought me. 😊


Python syntax hacks
===================

bidict used to support
`slice syntax <https://bidict.readthedocs.io/en/v0.9.0.post1/intro.html#bidict-bidict>`__
for looking up keys by value:

.. code-block:: python

   >>> element_by_symbol = bidict(H='hydrogen')
   >>> element_by_symbol['H']  # normal syntax for the forward mapping
   'hydrogen'
   >>> element_by_symbol[:'hydrogen']  # :slice syntax for the inverse
   'H'

See `this code <https://github.com/jab/bidict/blob/356dbe3/bidict/_bidict.py#L25>`__
for how this was implemented,
and `#19 <https://github.com/jab/bidict/issues/19>`__ for why this was dropped.


Efficient ordered mappings
==========================

**It's a real, live, industrial-strength linked list in the wild!**
If you've only ever seen the tame kind in those boring data structures courses,
you may be in for a treat:
see `_orderedbase.py <https://github.com/jab/bidict/blob/master/bidict/_orderedbase.py#L10>`__.
Inspired by Python's own :class:`~collections.OrderedDict`
`implementation <https://github.com/python/cpython/blob/a0374d/Lib/collections/__init__.py#L71>`_.


Property-based testing is amazing
=================================

Dramatically increase test coverage by
asserting that your properties hold for ~all valid inputs.
Don't just automatically run the testcases you happened to think of manually,
generate your testcases automatically
(and a whole lot more of the ones you'd never think of) too.

Bidict never would have survived so many refactorings with so few bugs
if it weren't for property-based testing, enabled by the amazing
`Hypothesis <https://hypothesis.readthedocs.io>`__ library.
It's game-changing.

See `bidict's property-based tests
<https://github.com/jab/bidict/blob/master/tests/hypothesis/test_properties.py>`__.


Python's surprises, gotchas, and a mistake
==========================================

- See :ref:`addendum:nan as key`.

- See :ref:`addendum:Equivalent but distinct \:class\:\`~collections.abc.Hashable\`\\s`.

- What should happen when checking equality of several ordered mappings
  that contain the same items but in a different order?
  What about when comparing with an unordered mapping?

  Check out what Python's :class:`~collections.OrderedDict` does,
  and the surprising results:

  .. code-block:: python

     >>> from collections import OrderedDict
     >>> d = dict([(0, 1), (2, 3)])
     >>> od = OrderedDict([(0, 1), (2, 3)])
     >>> od2 = OrderedDict([(2, 3), (0, 1)])
     >>> d == od
     True
     >>> d == od2
     True
     >>> od == od2
     False

     >>> class MyDict(dict):
     ...   __hash__ = lambda self: 0
     ...

     >>> class MyOrderedDict(OrderedDict):
     ...   __hash__ = lambda self: 0
     ...

     >>> d = MyDict([(0, 1), (2, 3)])
     >>> od = MyOrderedDict([(0, 1), (2, 3)])
     >>> od2 = MyOrderedDict([(2, 3), (0, 1)])
     >>> len({d, od, od2})
     1
     >>> len({od, od2, d})
     2

  According to Raymond Hettinger (the author of :class:`~collections.OrderedDict`),
  this design was a mistake
  (it violates the `Liskov substitution principle
  <https://en.wikipedia.org/wiki/Liskov_substitution_principle>`__),
  but it's too late now to fix.

  Fortunately, it wasn't too late for bidict to learn from this.
  Hence :ref:`eq-order-insensitive` for ordered bidicts,
  and their separate :meth:`~bidict.FrozenOrderedBidict.equals_order_sensitive` method.


Python's data model
===================

- What happens when you implement a custom :meth:`~object.__eq__`?
  e.g. What's the difference between ``a == b`` and ``b == a``
  when only ``a`` is an instance of your class?
  See the great write-up in https://eev.ee/blog/2012/03/24/python-faq-equality/
  for the answer.

- If an instance of your special mapping type
  is being compared against a mapping of some foreign mapping type
  that contains the same items,
  should your ``__eq__()`` method return true?

  bidict says yes, again based on the `Liskov substitution principle
  <https://en.wikipedia.org/wiki/Liskov_substitution_principle>`__.
  Only returning true when the types matched exactly would violate this.
  And returning :obj:`NotImplemented` would cause Python to fall back on
  using identity comparison, which is not what is being asked for.

  (Just for fun, suppose you did only return true when the types matched exactly,
  and suppose your special mapping type were also hashable.
  Would it be worth having your ``__hash__()`` method include your type
  as well as your items?
  The only point would be to reduce collisions when multiple instances of different
  types contained the same items
  and were going to be inserted into the same :class:`dict` or :class:`set`,
  since they'd now be unequal but would hash to the same value otherwise.)

- Making an immutable type hashable
  (so it can be inserted into :class:`dict`\s and :class:`set`\s):
  Must implement :meth:`~object.__hash__` such that
  ``a == b ⇒ hash(a) == hash(b)``.
  See the :meth:`object.__hash__` and :meth:`object.__eq__` docs, and
  the `implementation <https://github.com/jab/bidict/blob/master/bidict/_frozenbidict.py#L10>`__
  of :class:`~bidict.frozenbidict`.

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
      CPython? The only way to use it is to call ``hash(frozenset(self.items()))``,
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
    that override :meth:`~object.__eq__`
    are not hashable by default.

- Using :meth:`~object.__new__` to bypass default object initialization,
  e.g. for better :meth:`~bidict.bidict.copy` performance.
  See `_base.py <https://github.com/jab/bidict/blob/master/bidict/_bidict.py#L10>`__.

- Overriding :meth:`object.__getattribute__` for custom attribute lookup.
  See :ref:`extending:Sorted Bidict Recipes`.

- Using
  :meth:`object.__getstate__`,
  :meth:`object.__setstate__`, and
  :meth:`object.__reduce__` to make an object pickleable
  that otherwise wouldn't be,
  due to e.g. using weakrefs,
  as bidicts do (covered further below).


Better memory usage through ``__slots__``
=========================================

Using :ref:`slots` dramatically reduces memory usage in CPython
and speeds up attribute access to boot.
Must be careful with pickling and weakrefs though!
See `BidictBase.__getstate__()
<https://github.com/jab/bidict/blob/master/bidict/_base.py>`__.


Better memory usage through :mod:`weakref`
==========================================

A bidict and its inverse use :mod:`weakref`
to avoid creating a strong reference cycle,
so that when you release your last reference to a bidict,
its memory is reclaimed immediately in CPython
rather than having to wait for the next garbage collection.
See :ref:`addendum:Bidict Avoids Reference Cycles`.

The (doubly) linked lists that back ordered bidicts also use weakrefs
to avoid creating strong reference cycles.


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

.. doctest::

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

See the `implementation
<https://github.com/jab/bidict/blob/master/bidict/_named.py>`__
of :func:`~bidict.namedbidict`.


API Design
==========

How to deeply integrate with Python's :mod:`collections`?

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

- How to make your own open ABC like :class:`~collections.abc.Hashable`?

  - Override :meth:`~abc.ABCMeta.__subclasshook__`
    to check for the interface you require.
    See the `implementation
    <https://github.com/jab/bidict/blob/master/bidict/_abc.py#L10>`__
    of :class:`~bidict.BidirectionalMapping`.

  - Interesting consequence of the ``__subclasshook__()`` design:
    the "subclass" relation becomes intransitive.
    e.g. :class:`object` is a subclass of :class:`~collections.abc.Hashable`,
    :class:`list` is a subclass of :class:`object`,
    but :class:`list` is not a subclass of :class:`~collections.abc.Hashable`.

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

How to make APIs Pythonic?

- See the `Zen of Python <https://www.python.org/dev/peps/pep-0020/>`__.

- "Errors should never pass silently.

  Unless explicitly silenced.

  In the face of ambiguity, refuse the temptation to guess."

  Manifested in bidict's default duplication policies.

- "Readability counts."

  "There should be one – and preferably only one – obvious way to do it."

  An early version of bidict allowed using the ``~`` operator to access ``.inverse``
  and a special slice syntax like ``b[:val]`` to look up a key by value,
  but these were removed in preference to the more obvious and readable
  ``.inverse``-based spellings.


Portability
===========

- Python 2 vs. Python 3

  - Mostly :class:`dict` API changes,
    but also functions like :func:`zip`, :func:`map`, :func:`filter`, etc.

  - If you define a custom :meth:`~object.__eq__` on a class,
    it will *not* be used for ``!=`` comparisons on Python 2 automatically;
    you must explicitly add an :meth:`~object.__ne__` implementation
    that calls your :meth:`~object.__eq__` implementation.
    If you don't, :meth:`object.__ne__` will be used instead,
    which behaves like ``is not``.
    GOTCHA alert!

    Python 3 thankfully fixes this.

  - Borrowing methods from other classes:

    In Python 2, must grab the ``.im_func`` / ``__func__``
    attribute off the borrowed method to avoid getting
    ``TypeError: unbound method ...() must be called with ... instance as first argument``

    See the `implementation <https://github.com/jab/bidict/blob/master/bidict/_frozenordered.py#L10>`__
    of :class:`~bidict.FrozenOrderedBidict`.

- CPython vs. PyPy

  - gc / weakref

  - primitives' identities, nan, etc.

    - https://bitbucket.org/pypy/pypy/src/dafacc4/pypy/doc/cpython_differences.rst?mode=view

    - Hence ``test_no_reference_cycles()``
      in `test_properties.py
      <https://github.com/jab/bidict/blob/master/tests/hypothesis/test_properties.py>`__
      is skipped on PyPy.


Other interesting stuff in the standard library
===============================================

- :mod:`reprlib` and :func:`reprlib.recursive_repr`
  (but not needed for bidict because there's no way to insert a bidict into itself)
- :func:`operator.methodcaller`
- :attr:`platform.python_implementation`
- See :ref:`addendum:Missing bidicts in Stdlib!`


Tools
=====

See :ref:`thanks:Projects` for some of the fantastic tools
for software verification, performance, code quality, etc.
that bidict has provided an excuse to play with and learn.

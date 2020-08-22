Learning from ``bidict``
------------------------

Below is an outline of some of the more fascinating
and lesser-known Python corners I got to explore further
thanks to working on :mod:`bidict`.

If you would like to learn more about any of the topics below,
you may find `reading bidict's code
<https://github.com/jab/bidict/blob/master/bidict/__init__.py#L10>`__
particularly interesting.

I've sought to optimize the code not just for correctness and performance,
but also to make for a clear and enjoyable read,
illuminating anything that could otherwise be obscure or subtle.

I hope it brings you some of the
`joy <https://joy.recurse.com/posts/148-bidict>`__
it's brought me. 😊


Python syntax hacks
===================

:mod:`bidict` used to support
(ab)using a specialized form of Python's :ref:`slice <slicings>` syntax
for getting and setting keys by value:

.. code-block:: python

   >>> element_by_symbol = bidict(H='hydrogen')
   >>> element_by_symbol['H']  # [normal] syntax for the forward mapping
   'hydrogen'
   >>> element_by_symbol[:'hydrogen']  # [:slice] syntax for the inverse (no longer supported)
   'H'

See `this code <https://github.com/jab/bidict/blob/356dbe3/bidict/_bidict.py#L25>`__
for how this was implemented,
and `#19 <https://github.com/jab/bidict/issues/19>`__ for why this was dropped.


Code structure
==============

:class:`~bidict.bidict`\s come in every combination of
mutable, immutable, ordered, and unordered types,
implementing Python's various
:class:`relevant <collections.abc.Mapping>`
:class:`collections <collections.abc.MutableMapping>`
:class:`interfaces <collections.abc.Hashable>`
as appropriate.

Factoring the code to maximize reuse, modularity, and
adherence to `SOLID <https://en.wikipedia.org/wiki/SOLID>`__ design principles
(while not missing any chances for special-case optimizations)
has been one of the most fun parts of working on bidict.

To see how this is done, check out this code:

- `_base.py <https://github.com/jab/bidict/blob/master/bidict/_base.py#L10>`__
- `_delegating.py <https://github.com/jab/bidict/blob/master/bidict/_delegating.py#L12>`__
- `_frozenbidict.py <https://github.com/jab/bidict/blob/master/bidict/_frozenbidict.py#L10>`__
- `_mut.py <https://github.com/jab/bidict/blob/master/bidict/_mut.py#L10>`__
- `_bidict.py <https://github.com/jab/bidict/blob/master/bidict/_bidict.py#L10>`__
- `_orderedbase.py <https://github.com/jab/bidict/blob/master/bidict/_orderedbase.py#L10>`__
- `_frozenordered.py <https://github.com/jab/bidict/blob/master/bidict/_frozenordered.py#L10>`__
- `_orderedbidict.py <https://github.com/jab/bidict/blob/master/bidict/_orderedbidict.py#L10>`__

Data structures are amazing
===========================

Data structures are one of the most fascinating and important
building blocks of programming and computer science.

It's all too easy to lose sight of the magic when having to implement them
for computer science courses or job interview questions.
Part of this is because many of the most interesting real-world details get left out,
and you miss all the value that comes from ongoing, direct practical application.

Bidict shows how fundamental data structures
can be implemented in Python for important real-world usage,
with practical concerns at top of mind.
Come to catch sight of a real, live, industrial-strength linked list in the wild.
Stay for the rare, exotic bidirectional mapping breeds you'll rarely see at home.
[#fn-data-struct]_

.. [#fn-data-struct] To give you a taste:

   A regular :class:`~bidict.bidict`
   encapsulates two regular dicts,
   keeping them in sync to preserve the bidirectional mapping invariants.
   Since dicts are unordered, regular bidicts are unordered too.
   How should we extend this to implement an ordered bidict?

   We'll still need two backing mappings to store the forward and inverse associations.
   To store the ordering, we use a (circular, doubly-) linked list.
   This allows us to e.g. delete an item in any position in O(1) time.

   Interestingly, the nodes of the linked list encode only the ordering of the items;
   the nodes themselves contain no key or value data.
   The two backing mappings associate the key and value data
   with the nodes, providing the final pieces of the puzzle.

   Can we use dicts for the backing mappings, as we did for the unordered bidict?
   It turns out that dicts aren't enough—the backing mappings must actually be
   (unordered) bidicts themselves!

Check out `_orderedbase.py <https://github.com/jab/bidict/blob/master/bidict/_orderedbase.py#L10>`__
to see this in action.


Property-based testing is revolutionary
=======================================

When your automated tests run,
are they only checking the test cases
you happened to hard-code into your test suite?
How do you know these test cases aren't missing
some important edge cases?

With property-based testing,
you describe the types of test case inputs your functions accept,
along with the properties that should hold for all inputs.
Rather than having to think up your test case inputs manually
and hard-code them into your test suite,
they get generated for you dynamically,
in much greater quantity and edge case-exercising diversity
than you could come up with by hand.
This dramatically increases test coverage
and confidence that your code is correct.

Bidict never would have survived so many refactorings with so few bugs
if it weren't for property-based testing, enabled by the amazing
`Hypothesis <https://hypothesis.readthedocs.io>`__ library.
It's game-changing.

Check out `bidict's property-based tests
<https://github.com/jab/bidict/blob/master/tests/properties/test_properties.py>`__
to see this in action.


Python surprises, gotchas, regrets
==================================

- See :ref:`addendum:\*nan\* as a Key`.

- See :ref:`addendum:Equivalent but distinct \:class\:\`~collections.abc.Hashable\`\\s`.

- What should happen when checking equality of several ordered mappings
  that contain the same items but in a different order?
  What about when comparing with an unordered mapping?

  Check out what Python's :class:`collections.OrderedDict` does,
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

  According to Raymond Hettinger
  (Python core developer responsible for much of Python's collections),
  this design was a mistake
  (e.g. it violates the `Liskov substitution principle
  <https://en.wikipedia.org/wiki/Liskov_substitution_principle>`__
  and the `transitive property of equality
  <https://en.wikipedia.org/wiki/Equality_(mathematics)#Basic_properties>`__),
  but it's too late now to fix.

  Fortunately, it wasn't too late for bidict to learn from this.
  Hence :ref:`eq-order-insensitive` for ordered bidicts,
  and their separate :meth:`~bidict.FrozenOrderedBidict.equals_order_sensitive` method.

- If you define a custom :meth:`~object.__eq__` on a class,
  it will *not* be used for ``!=`` comparisons on Python 2 automatically;
  you must explicitly add an :meth:`~object.__ne__` implementation
  that calls your :meth:`~object.__eq__` implementation.
  If you don't, :meth:`object.__ne__` will be used instead,
  which behaves like ``is not``. Python 3 thankfully fixes this.


Better memory usage through ``__slots__``
=========================================

Using :ref:`slots` dramatically reduces memory usage in CPython
and speeds up attribute access to boot.
Must be careful with pickling and weakrefs though!
See `BidictBase.__getstate__()
<https://github.com/jab/bidict/blob/master/bidict/_base.py>`__.


Better memory usage through :mod:`weakref`
==========================================

A :class:`~bidict.bidict` and its inverse use :mod:`weakref`
to avoid creating a strong reference cycle,
so that when you release your last reference to a bidict,
its memory is reclaimed immediately in CPython
rather than having to wait for the next garbage collection.
See :ref:`addendum:\`\`bidict\`\` Avoids Reference Cycles`.

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

Here's an example:

.. doctest::

   >>> from collections import namedtuple
   >>> from itertools import count

   >>> class Node(namedtuple('_Node', 'cost tiebreaker data parent depth')):
   ...     """Represent nodes in a graph traversal. Suitable for use with e.g. heapq."""
   ...
   ...     __slots__ = ()
   ...     _counter = count()  # break ties between equal-cost nodes, avoid comparing data
   ...
   ...     # Give call sites a cleaner API for creating new Nodes
   ...     def __new__(cls, cost, data, parent=None):
   ...         tiebreaker = next(cls._counter)
   ...         depth = parent.depth + 1 if parent else 0
   ...         return super().__new__(cls, cost, tiebreaker, data, parent, depth)
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

How to deeply integrate with Python's :mod:`collections` and other built-in APIs?

- Beyond implementing :class:`collections.abc.Mapping`,
  bidicts implement additional APIs
  that :class:`dict` and :class:`~collections.OrderedDict` implement
  (e.g. :meth:`setdefault`, :meth:`popitem`, etc.).

  - When creating a new API, making it familiar, memorable, and intuitive
    is hugely important to a good user experience.

- Thanks to :class:`~collections.abc.Hashable`'s
  implementing :meth:`abc.ABCMeta.__subclasshook__`,
  any class that implements the required methods of the
  :class:`~collections.abc.Hashable` interface
  (namely, :meth:`~collections.abc.Hashable.__hash__`)
  makes it a virtual subclass already, no need to explicitly extend.
  I.e. As long as ``Foo`` implements a ``__hash__()`` method,
  ``issubclass(Foo, Hashable)`` will always be True,
  no need to explicitly subclass via ``class Foo(Hashable): ...``

- How to make your own open ABC like :class:`~collections.abc.Hashable`?

  - Override :meth:`~abc.ABCMeta.__subclasshook__`
    to check for the interface you require.
    See :class:`~bidict.BidirectionalMapping`'s
    `old (correct) implementation
    <https://github.com/jab/bidict/blob/v0.14.2/bidict/_abc.py>`__
    (this was later removed due to lack of use and maintenance cost
    when it was discovered that a bug was introduced in v0.15.0).

  - Interesting consequence of the ``__subclasshook__()`` design:
    the "subclass" relation becomes intransitive.
    e.g. :class:`object` is a subclass of :class:`~collections.abc.Hashable`,
    :class:`list` is a subclass of :class:`object`,
    but :class:`list` is not a subclass of :class:`~collections.abc.Hashable`.

- What if you needed to derive from a second metaclass?
  Be careful to avoid
  "TypeError: metaclass conflict: the metaclass of a derived class
  must be a (non-strict) subclass of the metaclasses of all its bases".
  See the great write-up in
  https://blog.ionelmc.ro/2015/02/09/understanding-python-metaclasses/.

- :class:`collections.abc.Mapping` and
  :class:`collections.abc.MutableMapping`
  don't implement :meth:`~abc.ABCMeta.__subclasshook__`,
  so you must either explicitly subclass them
  (in which case you inherit their concrete method implementations)
  or use :meth:`abc.ABCMeta.register`
  (to register as a virtual subclass without inheriting any of the implementation).

- Notice that Python provides :class:`collections.abc.Reversible`
  but no ``collections.abc.Ordered`` or ``collections.abc.OrderedMapping``.
  This was proposed in `bpo-28912 <https://bugs.python.org/issue28912>`__ but rejected.
  Would have been useful for bidict's ``__repr__()`` implementation (see ``_base.py``),
  and potentially for interop with other ordered mapping implementations
  such as `SortedDict <http://www.grantjenks.com/docs/sortedcontainers/sorteddict.html>`__.

How to make APIs Pythonic?

- See the `Zen of Python <https://www.python.org/dev/peps/pep-0020/>`__.

- "Errors should never pass silently.

  Unless explicitly silenced.

  In the face of ambiguity, refuse the temptation to guess."

  Manifested in bidict's default :attr:`~bidict.bidict.on_dup` class attribute
  (see :attr:`~bidict.ON_DUP_DEFAULT`).

- "Readability counts."

  "There should be one – and preferably only one – obvious way to do it."

  An early version of bidict allowed using the ``~`` operator to access ``.inverse``
  and a special slice syntax like ``b[:val]`` to look up a key by value,
  but these were removed in preference to the more obvious and readable
  ``.inverse``-based spellings.


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

  Bidict says yes, again based on the `Liskov substitution principle
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
  See :ref:`extending:\`\`SortedBidict\`\` Recipes`.

- Using
  :meth:`object.__getstate__`,
  :meth:`object.__setstate__`, and
  :meth:`object.__reduce__` to make an object pickleable
  that otherwise wouldn't be,
  due to e.g. using weakrefs,
  as bidicts do (covered further below).


Portability
===========

- Python 2 vs. Python 3

  - As affects bidict, mostly :class:`dict` API changes,
    but also functions like :func:`zip`, :func:`map`, :func:`filter`, etc.

  - See the :meth:`~object.__ne__` gotcha for Python 2 above.

  - Borrowing methods from other classes:

    In Python 2, must grab the ``.im_func`` / ``__func__``
    attribute off the borrowed method to avoid getting
    ``TypeError: unbound method ...() must be called with ... instance as first argument``

    See the `old implementation <https://github.com/jab/bidict/blob/v0.18.3/bidict/_frozenordered.py#L10>`__
    of :class:`~bidict.FrozenOrderedBidict`.

- CPython vs. PyPy (and other Python implementations)

  - See https://doc.pypy.org/en/latest/cpython_differences.html

  - gc / weakref

  - Hence ``test_bidicts_freed_on_zero_refcount()``
    in `test_properties.py
    <https://github.com/jab/bidict/blob/master/tests/properties/test_properties.py>`__
    is skipped outside CPython.

  - primitives' identities, nan, etc.


Other interesting stuff in the standard library
===============================================

- :mod:`reprlib` and :func:`reprlib.recursive_repr`
  (but not needed for bidict because there's no way to insert a bidict into itself)
- :func:`operator.methodcaller`
- See :ref:`addendum:Missing \`\`bidict\`\`\\s in the Standard Library`


Tools
=====

See the :ref:`Thanks <thanks:Projects>` page for some of the fantastic tools
for software verification, performance, code quality, etc.
that bidict has provided an excuse to play with and learn.

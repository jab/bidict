Learning from ``bidict``
------------------------

Working on :mod:`bidict` has taken me to
some of the most interesting and unexpected places
I've ever gotten to visit in many years of programming.
(When I started this project ~15 years ago,
I'd never heard of things like higher-kinded types.
Thanks to :mod:`bidict`, I not only came across them,
I even got to `share a practical, real-world example with Guido
<https://github.com/python/typing/issues/548#issuecomment-621195693>`__
where they would be beneficial for Python.)

The problem space that :mod:`bidict` inhabits
is abundant with beautiful symmetries,
delightful surprises, and rich opportunities
to come up with elegant solutions.

You can check out :mod:`bidict`'s source
to see for yourself.
I've sought to optimize the code
not just for correctness and performance,
but also for clarity, maintainability,
and to make for an enjoyable read.

See below for more, and feel free to
let me know what you think.
I hope reading :mod:`bidict`'s code
brings you some of the
`joy <https://joy.recurse.com/posts/148-bidict>`__
that :mod:`bidict` has brought me.


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
(while not missing any chances for specialized optimizations)
has been one of the most fun parts of working on bidict.

To see how this is done, check out the code starting with
`__init__.py <https://github.com/jab/bidict/blob/main/bidict/__init__.py#L9>`__,
and then follow the path suggested in the "code review nav" comments at the
top of the file:

- `_base.py <https://github.com/jab/bidict/blob/main/bidict/_base.py#L8>`__
- `_frozenbidict.py <https://github.com/jab/bidict/blob/main/bidict/_frozenbidict.py#L8>`__
- `_bidict.py <https://github.com/jab/bidict/blob/main/bidict/_bidict.py#L8>`__
- `_orderedbase.py <https://github.com/jab/bidict/blob/main/bidict/_orderedbase.py#L8>`__
- `_frozenordered.py <https://github.com/jab/bidict/blob/main/bidict/_frozenordered.py#L8>`__
- `_orderedbidict.py <https://github.com/jab/bidict/blob/main/bidict/_orderedbidict.py#L8>`__


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

.. admonition:: To give you a taste...

   A regular :class:`~bidict.bidict`
   encapsulates two regular dicts,
   keeping them in sync to preserve the bidirectional mapping invariants.
   Since dicts are unordered, regular bidicts are unordered too.
   How should we extend this to implement an ordered bidict?

   :class:`~bidict.OrderedBidictBase` inherits from
   :class:`~bidict.BidictBase` the use of two regular dicts
   to store the forward and inverse associations.
   And to store the ordering of the associations,
   we use a doubly-linked list.
   This allows us to e.g. move any item to the front
   of the ordering in O(1) time.

   Interestingly, the nodes of the linked list encode only the ordering of the items;
   the nodes themselves contain no key or value data.
   An additional backing mapping associates the key/value data
   with the nodes, providing the final piece of the puzzle.

   And since :class:`~bidict.OrderedBidictBase` needs to not only
   look up nodes by key/value, but also key/value by node,
   it uses an (unordered) :class:`~bidict.bidict` for this internally.
   Bidicts all the way down!


Python syntax hacks
===================

:mod:`bidict` used to support
(ab)using a specialized form of Python's :ref:`slice <slicings>` syntax
for getting and setting keys by value:

.. code-block:: python

   element_by_symbol = bidict(H='hydrogen')
   # [normal] syntax for the forward mapping lookup:
   element_by_symbol['H']  # ==> 'hydrogen'
   # [:slice] syntax for the inverse lookup (no longer supported):
   element_by_symbol[:'hydrogen']  # ==> 'H'

See `this code <https://github.com/jab/bidict/blob/356dbe3/bidict/_bidict.py#L25>`__
for how this was implemented,
and :issue:`19` for why this was dropped.


Property-based testing is indispensable
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

Check out `bidict's property-based tests
<https://github.com/jab/bidict/blob/main/tests/property_tests/test_properties.py>`__
to see this in action.


Python surprises
================

- What should happen when checking equality of several ordered mappings
  that contain the same items but in a different order?

  What about when comparing an ordered mapping with an unordered mapping?

  First let's see how :class:`collections.OrderedDict` works.
  The results may surprise you:

  .. doctest::

     >>> from collections import OrderedDict
     >>> x = OrderedDict({1: 1, 2: 2})
     >>> y = {1: 1, 2: 2}
     >>> z = OrderedDict({2: 2, 1: 1})
     >>> x == y
     True
     >>> y == z
     True
     >>> x == z
     False

  So :class:`collections.OrderedDict` violates the
  `transitive property of equality
  <https://en.wikipedia.org/wiki/Equality_(mathematics)#Basic_properties>`__.
  This can lead to some even more unusual behavior than the above.
  As an example, let's see what would happen if
  :class:`bidict.FrozenOrderedBidict.__eq__`
  behaved this way:

  .. doctest::

     >>> class BadFrozenOrderedBidict(FrozenOrderedBidict):
     ...     __hash__ = FrozenOrderedBidict.__hash__
     ...
     ...     def __eq__(self, other):  # (deliberately simplified)
     ...         # Override to be order-sensitive, like collections.OrderedDict:
     ...         return all(i == j for (i, j) in zip(self.items(), other.items()))


     >>> x = BadFrozenOrderedBidict({1: 1, 2: 2})
     >>> y = frozenbidict({1: 1, 2: 2})
     >>> z = BadFrozenOrderedBidict({2: 2, 1: 1})
     >>> assert x == y and y == z and x != z
     >>> set1 = {x, y, z}
     >>> len(set1)
     2
     >>> set2 = {y, x, z}
     >>> len(set2)
     1

  Gotcha alert!

  According to Raymond Hettinger,
  the Python core developer who built Python's collections foundation,
  if we had it to do over again,
  we would make :meth:`collections.OrderedDict.__eq__`
  order-insensitive.
  Making ``__eq__`` order-sensitive not only violates the transitive property of equality,
  but also the `Liskov substitution principle
  <https://en.wikipedia.org/wiki/Liskov_substitution_principle>`__.
  Unfortunately, it's too late now to fix this for :class:`collections.OrderedDict`.

  Fortunately though, it's not too late for bidict to learn from this.
  Hence :ref:`eq-order-insensitive`, even for ordered bidicts.
  For an order-sensitive equality check, bidict provides the separate
  :meth:`~bidict.BidictBase.equals_order_sensitive` method,
  thanks in no small part to `Raymond's good advice
  <https://groups.google.com/g/comp.lang.python/c/eGSPciKcbPk/m/z_L7Ko09DQAJ>`__.

- See :ref:`addendum:\*nan\* as a Key`.

- See :ref:`addendum:Equivalent but distinct \:class\:\`~collections.abc.Hashable\`\\s`.


Better memory usage through ``__slots__``
=========================================

Using :ref:`slots` speeds up attribute access,
and can dramatically reduce memory usage in CPython
when creating many instances of the same class.

As an example,
the ``Node`` class used internally by
:class:`~bidict.OrderedBidictBase`
to store the ordering of inserted items
uses slots for better performance at scale,
since as many node instances are kept in memory
as there are items in every ordered bidict in memory.
*See:* `_orderedbase.py <https://github.com/jab/bidict/blob/main/bidict/_orderedbase.py#L8>`__

(Note that extra care must be taken
when using slots with pickling and weakrefs.)


Better memory usage through :mod:`weakref`
==========================================

A :class:`~bidict.bidict` and its inverse use :mod:`weakref` to
:ref:`avoid creating a reference cycle
<addendum:\`\`bidict\`\` Avoids Reference Cycles>`.
As a result, when you drop your last reference to a bidict,
its memory is reclaimed immediately in CPython
rather than having to wait for the next garbage collection.
*See:* `_base.py <https://github.com/jab/bidict/blob/main/bidict/_base.py#L8>`__

As another example,
the ``Node`` class used internally by
:class:`~bidict.OrderedBidictBase`
uses weakrefs to avoid creating reference cycles
in the doubly-linked lists used
to encode the ordering of inserted items.
*See:* `_orderedbase.py <https://github.com/jab/bidict/blob/main/bidict/_orderedbase.py#L8>`__


Using descriptors for managed attributes
========================================

To abstract the details of creating and dereferencing
the weakrefs that :class:`~bidict.OrderedBidictBase`\'s
aforementioned doubly-linked list nodes use
to refer to their neighbor nodes,
a ``WeakAttr`` descriptor is used to
`manage access to these attributes automatically
<https://docs.python.org/3/howto/descriptor.html#managed-attributes>`__.
*See:* `_orderedbase.py <https://github.com/jab/bidict/blob/main/bidict/_orderedbase.py#L8>`__


The implicit ``__class__`` reference
====================================

Anytime you have to reference the exact class of an instance
(and not a potential subclass) from within a method body,
you can use the implicit, lexically-scoped ``__class__`` reference
rather than hard-coding the current class's name.
*See:* https://docs.python.org/3/reference/datamodel.html#executing-the-class-body


Subclassing :func:`~collections.namedtuple` classes
===================================================

To get the performance benefits, intrinsic sortability, etc.
of :func:`~collections.namedtuple`
while customizing behavior, state, API, etc.,
you can subclass a :func:`~collections.namedtuple` class.
(Make sure to include ``__slots__ = ()``,
if you want to keep the associated performance benefits –
see the section about slots above.)

See the *OnDup* class in
`_dup.py <https://github.com/jab/bidict/blob/main/bidict/_dup.py>`__
for an example.

Here's another example:

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
<https://github.com/jab/bidict/blob/main/bidict/_named.py>`__
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
  *See:* `<https://bugs.python.org/issue28912>`__

- See the `Zen of Python <https://www.python.org/dev/peps/pep-0020/>`__
  for how to make APIs Pythonic.

  The following Zen of Python guidelines have been particularly influential for bidict:
  - "Errors should never pass silently. Unless explicitly silenced.
  - "In the face of ambiguity, refuse the temptation to guess."
  - "Readability counts."
  - "There should be one – and preferably only one – obvious way to do it."


Python's data model
===================

- What happens when you implement a custom :meth:`~object.__eq__`?
  e.g. What's the difference between ``a == b`` and ``b == a``
  when only ``a`` is an instance of your class?
  See the great write-up in https://eev.ee/blog/2012/03/24/python-faq-equality/
  for the answer.

- Making an immutable type hashable
  (so it can be inserted into :class:`dict`\s and :class:`set`\s):
  Must implement :meth:`~object.__hash__` such that
  ``a == b ⇒ hash(a) == hash(b)``.
  See the :meth:`object.__hash__` and :meth:`object.__eq__` docs, and
  the `implementation <https://github.com/jab/bidict/blob/main/bidict/_frozenbidict.py#L8>`__
  of :class:`~bidict.frozenbidict`.

  - Consider :class:`~bidict.FrozenOrderedBidict`:
    its :meth:`~bidict.FrozenOrderedBidict.__eq__`
    is :ref:`order-insensitive <eq-order-insensitive>`.
    So all contained items must participate in the hash order-insensitively.

  - Can use `collections.abc.Set._hash
    <https://github.com/python/cpython/blob/v3.10.2/Lib/_collections_abc.py#L674>`__
    which provides a pure Python implementation of the same hash algorithm
    used to hash :class:`frozenset`\s.
    (Since :class:`~collections.abc.ItemsView` extends
    :class:`~collections.abc.Set`,
    :meth:`bidict.frozenbidict.__hash__`
    just calls ``ItemsView(self)._hash()``.)

    - See also `<https://bugs.python.org/issue46684>`__

  - Unlike other attributes, if a class implements ``__hash__()``,
    any subclasses of that class will not inherit it.
    It's like Python implicitly adds ``__hash__ = None`` to the body
    of every class that doesn't explicitly define ``__hash__``.
    So if you do want a subclass to inherit a base class's ``__hash__()``
    implementation, you have to set that manually,
    e.g. by adding ``__hash__ = BaseClass.__hash__`` in the class body.

    This is consistent with the fact that
    :class:`object` implements ``__hash__()``,
    but subclasses of :class:`object`
    that override :meth:`~object.__eq__`
    are not hashable by default.

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

- CPython vs. PyPy (and other Python implementations)

  - See https://doc.pypy.org/en/latest/cpython_differences.html

  - gc / weakref

  - Hence ``test_bidicts_freed_on_zero_refcount()``
    in `test_properties.py
    <https://github.com/jab/bidict/blob/main/tests/property_tests/test_properties.py>`__
    is skipped outside CPython.

  - primitives' identities, nan, etc.

- Python 2 vs. Python 3

  - As affects bidict, mostly :class:`dict` API changes,
    but also functions like :func:`zip`, :func:`map`, :func:`filter`, etc.

  - :meth:`~object.__ne__` fixed in Python 3

  - Borrowing methods from other classes:

    In Python 2, must grab the ``.im_func`` / ``__func__``
    attribute off the borrowed method to avoid getting
    ``TypeError: unbound method ...() must be called with ... instance as first argument``


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
that bidict has provided a great opportunity to learn and use.

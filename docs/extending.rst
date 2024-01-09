Extending ``bidict``
--------------------

Bidict was written with extensibility in mind.

Let's look at some examples.


``YoloBidict`` Recipe
#####################

If you'd like
:attr:`~bidict.ON_DUP_DROP_OLD`
to be the default :class:`~bidict.bidict.on_dup` behavior
(for :meth:`~bidict.bidict.__init__`,
:meth:`~bidict.bidict.__setitem__`, and
:meth:`~bidict.bidict.update`),
you can use the following recipe:

.. doctest::

   >>> from bidict import bidict, ON_DUP_DROP_OLD

   >>> class YoloBidict(bidict):
   ...     on_dup = ON_DUP_DROP_OLD

   >>> b = YoloBidict({'one': 1})
   >>> b['two'] = 1  # succeeds, no ValueDuplicationError
   >>> b
   YoloBidict({'two': 1})

   >>> b.update({'three': 1})  # ditto
   >>> b
   YoloBidict({'three': 1})

Of course, ``YoloBidict``'s inherited
:meth:`~bidict.bidict.put` and
:meth:`~bidict.bidict.putall` methods
still allow specifying a custom :class:`~bidict.OnDup`
per call via the *on_dup* argument,
and will both still default to raising for all duplication types.

Further demonstrating :mod:`bidict`'s extensibility,
to make an ``OrderedYoloBidict``,
the class above can simply inherit from
:class:`bidict.OrderedBidict`
rather than :class:`bidict.bidict`.


Beware of ``ON_DUP_DROP_OLD``
:::::::::::::::::::::::::::::

There's a good reason that :mod:`bidict` does not provide a ``YoloBidict`` out of the box.

Before you decide to use a ``YoloBidict`` in your own code,
beware of the following potentially unexpected, dangerous behavior:

.. doctest::

   >>> b = YoloBidict({'one': 1, 'two': 2})  # b contains two items
   >>> b['one'] = 2                          # update one of the items
   >>> b                                     # now b only has one item!
   YoloBidict({'one': 2})

As covered in :ref:`basic-usage:collapsing overwrites`,
setting an existing key to the value of a different existing item
causes both existing items to quietly collapse into a single new item.

The opposite customization would look something like:

.. doctest::

   >>> from bidict import ON_DUP_RAISE

   >>> class YodoBidict(bidict):  # yodo: you only die once!
   ...     on_dup = ON_DUP_RAISE

   >>> b = YodoBidict({'one': 1})
   >>> b['one'] = 2  # Unlike a regular bidict, YodoBidict won't allow this.
   Traceback (most recent call last):
       ...
   bidict.KeyDuplicationError: one
   >>> b
   YodoBidict({'one': 1})
   >>> b.forceput('one', 2)  # Any type of overwrite requires more force.
   >>> b
   YodoBidict({'one': 2})


``WeakrefBidict`` Recipe
########################

Suppose you need to store some objects in a bidict
without incrementing their refcounts.

With :class:`~bidict.BidictBase`\'s
:attr:`~bidict.BidictBase._fwdm_cls` (forward mapping class) and
:attr:`~bidict.BidictBase._invm_cls` (inverse mapping class) attributes,
accomplishing this is as simple as:

.. doctest::

   >>> from bidict import MutableBidict
   >>> from weakref import WeakKeyDictionary, WeakValueDictionary

   >>> class WeakrefBidict(MutableBidict):
   ...     _fwdm_cls = WeakKeyDictionary
   ...     _invm_cls = WeakValueDictionary

Now you can insert items into *WeakrefBidict* without incrementing their refcounts:

.. doctest::

   >>> b = WeakrefBidict()
   >>> o1, o2 = frozenset({1}), frozenset({2})
   >>> b[o1] = o2

Since o1 and o2 are the only strong references to these objects,
if you delete these references, the refcounts will go to zero
and the objects will immediately be deallocated on CPython,
since the *WeakrefBidict* isn't holding on to them:

.. use `:skipif: pypy` for the test below once https://github.com/thisch/pytest-sphinx/issues/9 is fixed

.. doctest::

   >>> del o1, o2  # after this, b immediately becomes empty on CPython:
   >>> if sys.implementation.name == 'cpython':
   ...     assert not b


``SortedBidict`` Recipes
########################

Suppose you need a bidict that maintains its items in sorted order.
The Python standard library does not include any sorted dict types,
but the excellent
`sortedcontainers <http://www.grantjenks.com/docs/sortedcontainers/>`__ and
`sortedcollections <http://www.grantjenks.com/docs/sortedcollections/>`__
libraries do.

Using these, along with :class:`~bidict.BidictBase`'s
:attr:`~bidict.BidictBase._fwdm_cls` (forward mapping class) and
:attr:`~bidict.BidictBase._invm_cls` (inverse mapping class) attributes,
creating a sorted bidict is simple:

.. doctest::

   >>> from sortedcontainers import SortedDict

   >>> class SortedBidict(MutableBidict):
   ...     """A sorted bidict whose forward items stay sorted by their keys,
   ...     and whose inverse items stay sorted by *their* keys.
   ...     Note: As a result, an instance and its inverse yield their items
   ...     in different orders.
   ...     """
   ...     _fwdm_cls = SortedDict
   ...     _invm_cls = SortedDict

   >>> b = SortedBidict({'Tokyo': 'Japan', 'Cairo': 'Egypt'})
   >>> b
   SortedBidict({'Cairo': 'Egypt', 'Tokyo': 'Japan'})

   >>> b['Lima'] = 'Peru'

   >>> list(b.items())  # stays sorted by key
   [('Cairo', 'Egypt'), ('Lima', 'Peru'), ('Tokyo', 'Japan')]

   >>> list(b.inverse.items())  # .inverse stays sorted by *its* keys (b's values)
   [('Egypt', 'Cairo'), ('Japan', 'Tokyo'), ('Peru', 'Lima')]


Here's a recipe for a sorted bidict whose forward items stay sorted by their keys,
and whose inverse items stay sorted by their values. i.e. An instance and its inverse
will yield their items in *the same* order:

.. doctest::

   >>> from sortedcollections import ValueSortedDict

   >>> class KeySortedBidict(MutableBidict):
   ...     _fwdm_cls = SortedDict
   ...     _invm_cls = ValueSortedDict

   >>> elem_by_atomicnum = KeySortedBidict({
   ...     6: 'carbon', 1: 'hydrogen', 2: 'helium'})

   >>> list(elem_by_atomicnum.items())  # stays sorted by key
   [(1, 'hydrogen'), (2, 'helium'), (6, 'carbon')]

   >>> list(elem_by_atomicnum.inverse.items())  # .inverse stays sorted by value
   [('hydrogen', 1), ('helium', 2), ('carbon', 6)]

   >>> elem_by_atomicnum[4] = 'beryllium'

   >>> list(elem_by_atomicnum.inverse.items())
   [('hydrogen', 1), ('helium', 2), ('beryllium', 4), ('carbon', 6)]


Automatic "Get Attribute" Pass-Through
######################################

Python makes it easy to customize a class's "get attribute" behavior.
You can take advantage of this to pass attribute access
through to the backing ``_fwdm`` mapping
when an attribute is not provided by the bidict class itself:

   >>> def __getattribute__(self, name):
   ...     try:
   ...         return object.__getattribute__(self, name)
   ...     except AttributeError:
   ...         return getattr(self._fwdm, name)

   >>> KeySortedBidict.__getattribute__ = __getattribute__

Now, even though this ``KeySortedBidict`` itself provides no ``peekitem`` attribute,
you can still call ``peekitem`` on it
and it will return the result of calling ``peekitem``
on the backing ``SortedDict``:

   >>> elem_by_atomicnum.peekitem()
   (6, 'carbon')


Dynamic Inverse Class Generation
################################

When a bidict class's
:attr:`~bidict.BidictBase._fwdm_cls` and
:attr:`~bidict.BidictBase._invm_cls`
are the same,
the bidict class is its own inverse class.
(This is the case for all the
:ref:`bidict classes <other-bidict-types:Bidict Types Diagram>`
that come with :mod:`bidict`.)

However, when a bidict's
:attr:`~bidict.BidictBase._fwdm_cls` and
:attr:`~bidict.BidictBase._invm_cls` differ,
as in the ``KeySortedBidict`` and ``WeakrefBidict`` recipes above,
the inverse class of the bidict
needs to have its
:attr:`~bidict.BidictBase._fwdm_cls` and
:attr:`~bidict.BidictBase._invm_cls` swapped.

:class:`~bidict.BidictBase` detects this
and dynamically computes the correct inverse class for you automatically.

You can see this if you inspect ``KeySortedBidict``'s inverse bidict:

   >>> elem_by_atomicnum.inverse.__class__.__name__
   'KeySortedBidictInv'

Notice that :class:`~bidict.BidictBase` automatically created a
``KeySortedBidictInv`` class and used it for the inverse bidict.

As expected, ``KeySortedBidictInv``'s
:attr:`~bidict.BidictBase._fwdm_cls` and
:attr:`~bidict.BidictBase._invm_cls`
are the opposite of ``KeySortedBidict``'s:

   >>> elem_by_atomicnum.inverse._fwdm_cls.__name__
   'ValueSortedDict'
   >>> elem_by_atomicnum.inverse._invm_cls.__name__
   'SortedDict'

:class:`~bidict.BidictBase` also ensures that round trips work as expected:

   >>> KeySortedBidictInv = elem_by_atomicnum.inverse.__class__  # i.e. a value-sorted bidict
   >>> atomicnum_by_elem = KeySortedBidictInv(elem_by_atomicnum.inverse)
   >>> atomicnum_by_elem
   KeySortedBidictInv({'hydrogen': 1, 'helium': 2, 'beryllium': 4, 'carbon': 6})
   >>> KeySortedBidict(atomicnum_by_elem.inverse) == elem_by_atomicnum
   True


-----

This all goes to show how simple it can be
to compose your own bidirectional mapping types
out of the building blocks that :mod:`bidict` provides.

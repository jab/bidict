Extending ``bidict``
--------------------

Although :mod:`bidict` provides the various bidirectional mapping types covered already,
it's possible that some use case might require something more than what's provided.
For this reason,
:mod:`bidict` was written with extensibility in mind.

Let's look at some examples.


YoloBidict Recipe
#################

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
   ...     __slots__ = ()
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
simply have the subclass above inherit from
:class:`bidict.OrderedBidict`
rather than :class:`bidict.bidict`.


Beware of ``ON_DUP_DROP_OLD``
:::::::::::::::::::::::::::::

There's a good reason that :mod:`bidict` does not provide a ``YoloBidict`` out of the box.

Before you decide to use a ``YoloBidict`` in your own code,
beware of the following potentially unexpected, dangerous behavior:

.. doctest::

   >>> b = YoloBidict({'one': 1, 'two': 2})  # contains two items
   >>> b['one'] = 2                          # update one of the items
   >>> b                                     # now only has one item!
   YoloBidict({'one': 2})

As covered in :ref:`basic-usage:Key and Value Duplication`,
setting an existing key to the value of a different existing item
causes both existing items to quietly collapse into a single new item.

A safer example of this type of customization would be something like:

.. doctest::

   >>> from bidict import ON_DUP_RAISE

   >>> class YodoBidict(bidict):
   ...     __slots__ = ()
   ...     on_dup = ON_DUP_RAISE

   >>> b = YodoBidict({'one': 1})
   >>> b['one'] = 2  # Works with a regular bidict, but Yodo plays it safe.
   Traceback (most recent call last):
       ...
   KeyDuplicationError: one
   >>> b
   YodoBidict({'one': 1})
   >>> b.forceput('one', 2)  # Any destructive change requires more force.
   >>> b
   YodoBidict({'one': 2})


Sorted Bidict Recipes
#####################

Suppose you need a bidict that maintains its items in sorted order.
The Python standard library does not include any sorted dict types,
but the excellent
`sortedcontainers <http://www.grantjenks.com/docs/sortedcontainers/>`__ and
`sortedcollections <http://www.grantjenks.com/docs/sortedcollections/>`__
libraries do.
Armed with these along with bidict's
:attr:`~bidict.BidictBase._fwdm_cls`
and
:attr:`~bidict.BidictBase._invm_cls`
attributes,
creating a sorted bidict type is dead simple:

.. doctest::

   >>> # As an optimization, bidict.bidict includes a mixin class that
   >>> # we can't use here (namely bidict._delegating_mixins._DelegateKeysAndItemsToFwdm),
   >>> # so extend the parent class, bidict.MutableBidict, instead.
   >>> from bidict import MutableBidict

   >>> import sortedcontainers

   >>> class SortedBidict(MutableBidict):
   ...     """A sorted bidict whose forward items stay sorted by their keys,
   ...     and whose inverse items stay sorted by *their* keys.
   ...     Note: As a result, an instance and its inverse yield their items
   ...     in different orders.
   ...     """
   ...     __slots__ = ()
   ...     _fwdm_cls = sortedcontainers.SortedDict
   ...     _invm_cls = sortedcontainers.SortedDict
   ...     _repr_delegate = list

   >>> b = SortedBidict({'Tokyo': 'Japan', 'Cairo': 'Egypt'})
   >>> b
   SortedBidict([('Cairo', 'Egypt'), ('Tokyo', 'Japan')])

   >>> b['Lima'] = 'Peru'

   >>> # b stays sorted by its keys:
   >>> list(b.items())
   [('Cairo', 'Egypt'), ('Lima', 'Peru'), ('Tokyo', 'Japan')]

   >>> # b.inverse stays sorted by *its* keys (b's values)
   >>> list(b.inverse.items())
   [('Egypt', 'Cairo'), ('Japan', 'Tokyo'), ('Peru', 'Lima')]


Here's a recipe for a sorted bidict whose forward items stay sorted by their keys,
and whose inverse items stay sorted by their values. i.e. An instance and its inverse
will yield their items in *the same* order:

.. doctest::

   >>> import sortedcollections

   >>> class KeySortedBidict(MutableBidict):
   ...     __slots__ = ()
   ...     _fwdm_cls = sortedcontainers.SortedDict
   ...     _invm_cls = sortedcollections.ValueSortedDict
   ...     _repr_delegate = list

   >>> element_by_atomic_number = KeySortedBidict({
   ...     3: 'lithium', 1: 'hydrogen', 2: 'helium'})

   >>> # stays sorted by key:
   >>> element_by_atomic_number
   KeySortedBidict([(1, 'hydrogen'), (2, 'helium'), (3, 'lithium')])

   >>> # .inverse stays sorted by value:
   >>> list(element_by_atomic_number.inverse.items())
   [('hydrogen', 1), ('helium', 2), ('lithium', 3)]

   >>> element_by_atomic_number[4] = 'beryllium'

   >>> list(element_by_atomic_number.inverse.items())
   [('hydrogen', 1), ('helium', 2), ('lithium', 3), ('beryllium', 4)]

   >>> # This works because a bidict whose _fwdm_cls differs from its _invm_cls computes
   >>> # its inverse class -- which (note) is not actually the same class as the original,
   >>> # as it needs to have its _fwdm_cls and _invm_cls swapped -- automatically.
   >>> # You can see this if you inspect the inverse bidict:
   >>> element_by_atomic_number.inverse  # Note the different class, which was auto-generated:
   KeySortedBidictInv([('hydrogen', 1), ('helium', 2), ('lithium', 3), ('beryllium', 4)])
   >>> ValueSortedBidict = element_by_atomic_number.inverse.__class__
   >>> ValueSortedBidict._fwdm_cls
   <class 'sortedcollections.recipes.ValueSortedDict'>
   >>> ValueSortedBidict._invm_cls
   <class 'sortedcontainers.sorteddict.SortedDict'>

   >>> # Round trips work as expected:
   >>> atomic_number_by_element = ValueSortedBidict(element_by_atomic_number.inverse)
   >>> atomic_number_by_element
   KeySortedBidictInv([('hydrogen', 1), ('helium', 2), ('lithium', 3), ('beryllium', 4)])
   >>> KeySortedBidict(atomic_number_by_element.inverse) == element_by_atomic_number
   True

   >>> # One other useful trick:
   >>> # To pass method calls through to the _fwdm SortedDict when not present
   >>> # on the bidict instance, provide a custom __getattribute__ method:
   >>> def __getattribute__(self, name):
   ...     try:
   ...         return object.__getattribute__(self, name)
   ...     except AttributeError as e:
   ...         return getattr(self._fwdm, name)

   >>> KeySortedBidict.__getattribute__ = __getattribute__

   >>> # bidict has no .peekitem attr, so the call is passed through to _fwdm:
   >>> element_by_atomic_number.peekitem()
   (4, 'beryllium')
   >>> element_by_atomic_number.inverse.peekitem()
   ('beryllium', 4)


Next proceed to :doc:`other-functionality`.

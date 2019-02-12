Extending ``bidict``
--------------------

Although bidict ships with all the bidict types we just covered,
it's always possible users might need something more than what's provided.
For this reason,
bidict was written with extensibility in mind.

Let's look at some examples.


OverwritingBidict Recipe
########################

If you'd like
:attr:`~bidict.OVERWRITE`
to be the default duplication policy for
:func:`~bidict.bidict.__setitem__` and
:func:`~bidict.bidict.update`,
rather than always having to use
:func:`~bidict.bidict.forceput` and
:func:`~bidict.bidict.forceupdate`,
you can use the following recipe:

.. doctest::

   >>> from bidict import bidict, OVERWRITE

   >>> class OverwritingBidict(bidict):
   ...     on_dup_val = OVERWRITE

   >>> b = OverwritingBidict({'one': 1})
   >>> b['two'] = 1  # succeeds, no ValueDuplicationError
   >>> b
   OverwritingBidict({'two': 1})

   >>> b.update({'three': 1})  # ditto
   >>> b
   OverwritingBidict({'three': 1})

As with
:class:`bidict.bidict`,
``OverwritingBidict.put()`` and
``OverwritingBidict.putall()``
will still provide per-call overrides for duplication policies,
and will both still default to raising for all duplication types
unless you override those methods too.

To make an overwriting *ordered* bidict,
simply adapt this recipe to have the class inherit from
:class:`bidict.OrderedBidict`.


Beware of ``OVERWRITE``
:::::::::::::::::::::::

With a default :attr:`~bidict.OVERWRITE` policy
as in the ``OverwritingBidict`` recipe above,
beware of the following potentially surprising behavior:

.. doctest::

   >>> b = OverwritingBidict({'one': 1, 'two': 2})
   >>> b['one'] = 2
   >>> b
   OverwritingBidict({'one': 2})

That is, setting an existing key to the value of a different existing item
causes both existing items to be collapsed into a single item.


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
   ...
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

.. _sorted-bidict-recipes:

Sorted Bidict Recipes
#####################

Suppose you need a bidict that maintains its items in sorted order.
The Python standard library does not include any sorted dict types,
but the excellent
`sortedcontainers <http://www.grantjenks.com/docs/sortedcontainers/>`_ and
`sortedcollections <http://www.grantjenks.com/docs/sortedcollections/>`_
libraries do.
Armed with these along with bidict's
:attr:`~bidict.BidictBase.fwdm_cls`
and
:attr:`~bidict.BidictBase.invm_cls`
attributes,
creating a sorted bidict type is dead simple::

    >>> import bidict, sortedcontainers

    >>> # a sorted bidict whose forward items stay sorted by their keys,
    >>> # and whose inverse items stay sorted by *their* keys (i.e. it and
    >>> # its inverse iterate over their items in different orders):

    >>> class KeySortedBidict(bidict.bidict):
    ...     fwdm_cls = sortedcontainers.SortedDict
    ...     invm_cls = sortedcontainers.SortedDict
    ...
    ...     # Include this for nicer repr's:
    ...     __repr_delegate__ = lambda x: list(x.items())

    >>> b = KeySortedBidict({'Tokyo': 'Japan', 'Cairo': 'Egypt'})
    >>> b
    KeySortedBidict([('Cairo', 'Egypt'), ('Tokyo', 'Japan')])

    >>> b['Lima'] = 'Peru'

    >>> # b stays sorted by its keys:
    >>> list(b.items())
    [('Cairo', 'Egypt'), ('Lima', 'Peru'), ('Tokyo', 'Japan')]

    >>> # b.inv stays sorted by *its* keys (b's values!)
    >>> list(b.inv.items())
    [('Egypt', 'Cairo'), ('Japan', 'Tokyo'), ('Peru', 'Lima')]


    >>> # a sorted bidict whose forward items stay sorted by their keys,
    >>> # and whose inverse items stay sorted by their values (i.e. it and
    >>> # its inverse iterate over their items in the same order):

    >>> import sortedcollections

    >>> class FwdKeySortedBidict(bidict.bidict):
    ...     fwdm_cls = sortedcontainers.SortedDict
    ...     invm_cls = sortedcollections.ValueSortedDict
    ...
    ...     # Include this for nicer repr's:
    ...     __repr_delegate__ = lambda x: list(x.items())

    >>> element_by_atomic_number = FwdKeySortedBidict({
    ...     3: 'lithium', 1: 'hydrogen', 2: 'helium'})

    >>> # stays sorted by key:
    >>> element_by_atomic_number
    FwdKeySortedBidict([(1, 'hydrogen'), (2, 'helium'), (3, 'lithium')])

    >>> # .inv stays sorted by value:
    >>> list(element_by_atomic_number.inv.items())
    [('hydrogen', 1), ('helium', 2), ('lithium', 3)]

    >>> element_by_atomic_number[4] = 'beryllium'

    >>> list(element_by_atomic_number.inv.items())
    [('hydrogen', 1), ('helium', 2), ('lithium', 3), ('beryllium', 4)]

    >>> # This works because a bidict whose fwdm_cls differs from its invm_cls calculates
    >>> # its inverse class (which has fwdm_cls and invm_cls swapped) automatically:
    >>> inv_cls = FwdKeySortedBidict.inv_cls()
    >>> inv_cls.__name__
    'FwdKeySortedBidictInv'
    >>> FwdKeySortedBidict.fwdm_cls is inv_cls.invm_cls
    True
    >>> FwdKeySortedBidict.invm_cls is inv_cls.fwdm_cls
    True

    >>> # To pass method calls through to the fwdm SortedDict when not present
    >>> # on the bidict instance, provide a custom __getattribute__ method:
    >>> def __getattribute__(self, name):
    ...     try:
    ...         return object.__getattribute__(self, name)
    ...     except AttributeError as e:
    ...         try:
    ...             return getattr(self.fwdm, name)
    ...         except AttributeError:
    ...             raise e

    >>> FwdKeySortedBidict.__getattribute__ = __getattribute__

    >>> # bidict has no .peekitem attr, so the call is passed through to fwdm:
    >>> element_by_atomic_number.peekitem()
    (4, 'beryllium')

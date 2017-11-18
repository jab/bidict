.. _sortedbidicts:

Sorted Bidict Recipes
#####################

Suppose you need a bidict that maintains its items in sorted order.
The Python standard library does not include any sorted dict types,
but the excellent
`sortedcontainers <http://www.grantjenks.com/docs/sortedcontainers/>`_ and
`sortedcollections <http://www.grantjenks.com/docs/sortedcollections/>`_
libraries do.
Armed with these along with bidict's
:attr:`_fwd_class <bidict.BidictBase._fwd_class>`
and
:attr:`_inv_class <bidict.BidictBase._inv_class>`
attributes,
creating a sorted bidict type is dead simple::

    >>> import bidict, sortedcontainers

    >>> # a sorted bidict whose forward items stay sorted by their keys,
    >>> # and whose inverse items stay sorted by *their* keys (i.e. it and
    >>> # its inverse iterate over their items in different orders):

    >>> class SortedBidict1(bidict.bidict):
    ...     _fwd_class = sortedcontainers.SortedDict
    ...     _inv_class = sortedcontainers.SortedDict
    ...     __reversed__ = lambda self: reversed(self._fwd)

    >>> b = SortedBidict1({'Tokyo': 'Japan', 'Cairo': 'Egypt'})
    >>> b
    SortedBidict1([('Cairo', 'Egypt'), ('Tokyo', 'Japan')])

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

    >>> class SortedBidict2(bidict.bidict):
    ...     _fwd_class = sortedcontainers.SortedDict
    ...     _inv_class = sortedcollections.ValueSortedDict
    ...     __reversed__ = lambda self: reversed(self._fwd)

    >>> element_by_atomic_number = SortedBidict2({
    ...     3: 'lithium', 1: 'hydrogen', 2: 'helium'})

    >>> # stays sorted by key:
    >>> element_by_atomic_number
    SortedBidict2([(1, 'hydrogen'), (2, 'helium'), (3, 'lithium')])

    >>> # .inv stays sorted by value:
    >>> list(element_by_atomic_number.inv.items())
    [('hydrogen', 1), ('helium', 2), ('lithium', 3)]

    >>> element_by_atomic_number[4] = 'beryllium'

    >>> list(element_by_atomic_number.inv.items())
    [('hydrogen', 1), ('helium', 2), ('lithium', 3), ('beryllium', 4)]

    >>> # order is preserved correctly when passing .inv back into constructor:
    >>> atomic_number_by_element = SortedBidict2(element_by_atomic_number.inv)
    >>> list(atomic_number_by_element.items()) == list(element_by_atomic_number.inv.items())
    True
    >>> # copies of .inv preserve order correctly too:
    >>> list(element_by_atomic_number.inv.copy().items()) == list(atomic_number_by_element.items())
    True

    >>> # To pass method calls through to the _fwd SortedDict when not present
    >>> # on the bidict instance, provide a custom __getattribute__ method:
    >>> def __getattribute__(self, name):
    ...     try:
    ...         return object.__getattribute__(self, name)
    ...     except AttributeError as e:
    ...         try:
    ...             return getattr(self._fwd, name)
    ...         except AttributeError:
    ...             raise e

    >>> SortedBidict2.__getattribute__ = __getattribute__

    >>> # bidict has no .peekitem attr, so the call is passed through to _fwd:
    >>> element_by_atomic_number.peekitem()
    (4, 'beryllium')

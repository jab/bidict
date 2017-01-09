"""Implements the frozen (immutable, hashable) bidict types."""

from ._common import BidictBase
from ._ordered import OrderedBidictBase
from .compat import PYPY, iteritems
from abc import abstractmethod
from collections import ItemsView
from itertools import chain, islice


class FrozenBidictBase(BidictBase):
    """Base class for frozen bidict types."""

    @abstractmethod
    def _compute_hash(self):
        """
        Abstract method to actually compute the hash.

        Default implementations are provided by
        :class:`frozenbidict` and :class:`frozenorderedbidict`,
        with tunable behavior via
        :attr:`_USE_ITEMSVIEW_HASH <frozenbidict._USE_ITEMSVIEW_HASH>` and
        :attr:`_HASH_NITEMS_MAX <frozenorderedbidict._HASH_NITEMS_MAX>`,
        respectively.

        If greater customization is needed,
        you can override this method in a subclass,
        but make sure you define :attr:`__hash__` in your subclass explicitly
        (e.g. "``__hash__ = FrozenBidictBase.__hash__``"), as Python does not
        resolve :attr:`__hash__` to a base class implementation through
        inheritance; it will implicitly be set to ``None`` if you don't.
        """
        return NotImplemented  # pragma: no cover

    def __hash__(self):
        """
        Return the hash of this frozen bidict from its contained items.

        Delegates to :attr:`_compute_hash` on the first call,
        then caches the result to make future calls *O(1)*.

        As a result, in the event that two distinct frozen bidict instances hash
        into the same bucket in a set or mapping, the time spent in ``__hash__``
        will generally be dominated by the time spent ``__eq__`` (which must be
        called to check if a hash collision between two unequal instances has
        actually occurred). If they are unequal, the ``__eq__`` call may short
        circuit in sublinear time, but in the worst case it will be *O(n)*. If
        they are equal, the call will always be *O(n)*. So, if inserting frozen
        bidicts into a set or mapping, the more items in the bidicts, the more
        the benefits of ``__hash__`` distributing unequal instances into
        different buckets.

        The result of :attr:`_compute_hash` is combined with the class in a
        final derived hash, to differentiate it from the hash of a different
        type of collection comprising the same items (e.g. frozenset or tuple).
        """
        if hasattr(self, '_hashval'):  # Cached on the first call.
            return self._hashval
        h = self._compute_hash()
        self._hashval = hv = hash((self.__class__, h))
        return hv


class frozenbidict(FrozenBidictBase):
    """
    Regular frozen bidict type.

    .. py:attribute:: _USE_ITEMSVIEW_HASH

        Defaults to ``True`` on PyPy and ``False`` otherwise.
        Override this to change the default behavior of :attr:`_compute_hash`.
        See :attr:`_compute_hash` for more information.

    """

    _USE_ITEMSVIEW_HASH = PYPY

    # Python sets __hash__ to None implicitly if not defined explicitly.
    def __hash__(self):  # Make its own method with its own docstring.
        """Delegate to :attr:`FrozenBidictBase.__hash__`."""
        return FrozenBidictBase.__hash__(self)

    def _compute_hash(self):
        """
        If :attr:`_USE_ITEMSVIEW_HASH` is ``True``,
        use the pure Python implementation of Python's frozenset hashing
        algorithm from ``collections.Set._hash`` to compute the hash
        incrementally in constant space.

        Otherwise, create an ephemeral frozenset out of the contained items
        and pass it to :func:`hash`. On CPython, this results in the faster
        ``frozenset_hash`` routine (implemented in ``setobject.c``) being used.
        CPython does not expose a way to use the fast C implementation of the
        algorithm without creating a frozenset.
        """
        # ItemsView(self)._hash() is faster than combining
        # KeysView(self)._hash() with KeysView(self.inv)._hash().
        if self._USE_ITEMSVIEW_HASH:
            return ItemsView(self)._hash()

        # frozenset(iteritems(self)) is faster than frozenset(ItemsView(self)).
        return hash(frozenset(iteritems(self)))


class frozenorderedbidict(OrderedBidictBase, FrozenBidictBase):
    """
    Ordered frozen bidict type.

    .. py:attribute:: _HASH_NITEMS_MAX

        The maximum number of items that participate in influencing the hash
        value. Defaults to ``None``, signifying that all items participate.
        Override to limit the time and space complexity of :attr:`_compute_hash`.
        See :attr:`_compute_hash` for more information.

    """

    _HASH_NITEMS_MAX = None

    # Python sets __hash__ to None implicitly if not defined explicitly.
    def __hash__(self):  # Make its own method with its own docstring.
        """Delegate to :attr:`FrozenBidictBase.__hash__`."""
        return FrozenBidictBase.__hash__(self)

    def _compute_hash(self):
        r"""
        Because items are ordered,
        this uses Python's tuple hashing algorithm
        to compute a hash of the contained items.

        Python does not expose a way to use its tuple hashing algorithm on an
        arbitrary iterable, so to use the algorithm, an ephemeral tuple from
        the contained items must be created and passed to :func:`hash`.
        i.e. The space complexity of this method is not constant. However,
        on CPython, this results in the ``tuplehash`` routine implemented in
        ``tupleobject.c`` being used, so this is faster than computing the hash
        incrementally in pure Python, which could be done in constant space.

        Time and space complexity can be bounded by overriding
        :attr:`_HASH_NITEMS_MAX` to limit the number of items that participate
        in influencing the hash value. This is safe because contained items
        have a guaranteed ordering, so not all items need to participate in the
        hash to guarantee that two equal :class:`frozenorderedbidict`\ s have
        the same hash value, as long as both use the same :attr:`_HASH_NITEMS_MAX`.
        """
        items = islice(iteritems(self), self._HASH_NITEMS_MAX)
        # Flatten [(k1, v1), (k2, v2), ...] to [k1, v1, k2, v2, ...] for a bit
        # of a speedup (avoids unnecessary recursive calls to tuplehash).
        # Ok because unflattened1 == unflattened2 <==> flattened1 == flattened2
        items = chain.from_iterable(items)
        return hash(tuple(items))

"""Implements the frozen (immutable, hashable) bidict types."""

from ._common import BidictBase, _marker
from ._ordered import OrderedBidictBase
from .compat import iteritems
from abc import abstractmethod
from itertools import chain, islice


class FrozenBidictBase(BidictBase):
    """
    Base class for frozen bidict types.

    .. py:attribute:: _HASH_NITEMS_MAX

        The maximum number of items that participate in influencing the hash
        value. Gives users the ability to bound the time and space complexity
        of an initial call to :attr:`__hash__` to a lower value than the total
        number of items, at the expense of a possible (but probably unlikely)
        increase in hash collisions for almost-equal instances.

        Defaults to ``None`` so that all items participate in influencing the
        hash value by default. This default may be reconsidered if it is shown
        that a different value is generally better. See discussion at
        <https://groups.google.com/d/topic/python-ideas/XcuC01a8SYs/discussion>.

        See :attr:`__hash__` for more information.

    """

    _HASH_NITEMS_MAX = None

    @abstractmethod
    def _compute_hash(self, items):
        """Abstract method to actually compute the hash of ``items``."""
        return NotImplemented  # pragma: no cover

    def __hash__(self):
        """
        Return the hash of this frozen bidict from its contained items.

        The number of participating items may be limited by
        :attr:`_HASH_NITEMS_MAX`.

        Delegates to :attr:`_compute_hash` on the first call, then caches the
        result to make future calls O(1).

        Creates an :func:`itertools.islice` of :attr:`_HASH_NITEMS_MAX` items
        and passes it to :attr:`_compute_hash`.
        A marker item derived from the class name is also prepended, to
        canonicalize the resulting hash.
        """
        if hasattr(self, '_hashval'):  # Cached on the first call.
            return self._hashval
        marker = _marker(self.__class__.__name__)
        marker = (marker, marker)  # shaped like an item to allow flattening
        items = islice(iteritems(self), self._HASH_NITEMS_MAX)
        items = chain((marker,), items)
        self._hashval = hv = self._compute_hash(items)
        return hv


class frozenbidict(FrozenBidictBase):
    """Regular frozen bidict type."""

    # Python sets __hash__ to None implicitly if not set explicitly.
    __hash__ = FrozenBidictBase.__hash__

    def _compute_hash(self, items):
        """
        Creates an ephemeral frozenset out of the given ``items``
        and returns the result of passing it to :func:`hash`.
        On CPython, this results in the fast ``frozenset_hash`` routine
        (implemented in ``setobject.c``) being used.

        CPython does not expose a way to use its fast C implementation of
        its set hashing algorithm with any iterable,
        so the ephemeral frozenset must be created to use it.
        A pure Python implementation of this algorithm is available in
        :func:`collections.Set._hash` which could be used instead
        to incrementally compute the hash in constant space,
        but it's noticeably slower than the C implementation,
        so it is not preferred here.

        Time and space complexity can be limited by setting
        :attr:`_HASH_NITEMS_MAX <FrozenBidictBase._HASH_NITEMS_MAX>`.

        PyPy users may prefer to override this in a subclass to return
        ``ItemsView(self)._hash()`` to avoid the ephemeral frozenset
        allocation, but it won't be any faster.
        """
        return hash(frozenset(items))


class frozenorderedbidict(OrderedBidictBase, FrozenBidictBase):
    """Ordered frozen bidict type."""

    # Python sets __hash__ to None implicitly if not set explicitly.
    __hash__ = FrozenBidictBase.__hash__

    def _compute_hash(self, items):
        """
        Because items are ordered, this uses Python's tuple hashing algorithm
        to compute a hash from ``items``.

        Python does not expose a way to use its tuple hashing algorithm on an
        iterable, so this creates an ephemeral tuple from ``items`` and returns
        the result of passing it to :func:`hash`.
        On CPython, this results in the fast ``tuplehash`` routine
        (implemented in ``tupleobject.c``) being used.

        Time and space complexity can be limited by setting
        :attr:`_HASH_NITEMS_MAX <FrozenBidictBase._HASH_NITEMS_MAX>`.
        """
        # Flatten items to avoid recursive calls to tuplehash. Noticeable speedup.
        # (k1, v1), (k2, v2), ...  ->  k1, v1, k2, v2, ...
        items = chain.from_iterable(items)
        return hash(tuple(items))

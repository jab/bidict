"""Implements the frozen (immutable, hashable) bidict types."""

from collections import ItemsView

from ._common import BidictBase
from ._ordered import OrderedBidictBase
from .compat import PYPY, iteritems


class FrozenBidict(BidictBase):  # lgtm [py/missing-equals]
    """
    Regular frozen bidict type.

    Provides a default implementation of :meth:`compute_hash`
    with tunable behavior via :attr:`USE_ITEMSVIEW_HASH`.

    If greater customization is needed,
    override :meth:`compute_hash` in a subclass.

    .. py:attribute:: USE_ITEMSVIEW_HASH

        Defaults to True on PyPy and False otherwise.
        Override this to change the default behavior of :attr:`compute_hash`.
        See :attr:`compute_hash` for more information.
    """

    USE_ITEMSVIEW_HASH = PYPY

    def compute_hash(self):
        """
        If :attr:`USE_ITEMSVIEW_HASH` is True,
        use the pure Python implementation of Python's frozenset hashing
        algorithm from ``collections.Set._hash`` to compute the hash
        incrementally in constant space.

        Otherwise, create an ephemeral :py:class:`frozenset` from the contained
        items and pass it to :func:`hash`. On CPython, this results in the faster
        ``frozenset_hash`` routine (implemented in ``setobject.c``) being used.
        CPython does not expose a way to use the fast C implementation of the
        algorithm without creating a frozenset.
        """
        if self.USE_ITEMSVIEW_HASH:
            return ItemsView(self)._hash()  # pylint: disable=protected-access
        itemsiter = iteritems(self)
        return hash(frozenset(itemsiter))

    def __hash__(self):
        """
        Return the hash of this frozen bidict from its contained items.

        Delegates to :attr:`compute_hash` on the first call,
        then caches the result to make future calls *O(1)*.
        """
        if hasattr(self, '_hash'):  # Cached on the first call.
            return self._hash  # pylint: disable=access-member-before-definition
        self._hash = self.compute_hash()  # pylint: disable=attribute-defined-outside-init
        return self._hash


class FrozenOrderedBidict(OrderedBidictBase, FrozenBidict):  # lgtm [py/missing-equals]
    r"""Ordered frozen bidict type.

    Inherits :class:`FrozenBidict`\'s
    :attr:`compute_hash <FrozenBidict.compute_hash>`
    implementation.

    This causes two :class:`FrozenOrderedBidict`\s with the same items
    in different order to get the same hash value even though they are unequal,
    leading to more hash collisions when inserting them into a set or mapping.
    However, this is necessary because a :class:`FrozenOrderedBidict` and a
    :class:`FrozenBidict` with the same items should compare equal, and so
    they must also hash to the same value.
    """

    # __hash__ must be set explicitly, will not be inherited from base class.
    __hash__ = FrozenBidict.__hash__

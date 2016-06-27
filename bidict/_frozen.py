"""Implements :class:`bidict.frozenbidict`."""

from .compat import viewitems
from ._common import BidirectionalMapping, _missing
from collections import Hashable


class frozenbidict(BidirectionalMapping, Hashable):
    """Immutable, hashable bidict type."""

    def __hash__(self):
        """Return the hash of this bidict."""
        h = getattr(self, '_hash', _missing)
        if h is not _missing:
            return h
        itemsview = viewitems(self)
        if hasattr(itemsview, '_hash'):  # e.g. collections.ItemsView._hash
            h = self._hash = itemsview._hash()
        else:
            h = self._hash = hash(tuple(itemsview))
        return h

"""Implements :class:`bidict.frozenbidict`."""

from .compat import viewitems
from ._common import BidirectionalMapping
from collections import Hashable


class frozenbidict(BidirectionalMapping, Hashable):
    """Immutable, hashable bidict type."""

    def __hash__(self):
        """Return the hash of this bidict."""
        if hasattr(self, '_hash'):
            return self._hash
        h = self._hash = hash(tuple(viewitems(self._fwd)))
        return h

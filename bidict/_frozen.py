"""Implements :class:`bidict.frozenbidict`."""

from .compat import viewitems
from ._common import BidirectionalMapping
from collections import Hashable

class frozenbidict(BidirectionalMapping, Hashable):
    """Immutable, hashable bidict type."""

    def __hash__(self):
        """Compute the hash of this bidict."""
        if self._hash is None:
            self._hash = hash(frozenset(viewitems(self)))
        return self._hash

"""Implements :class:`bidict.frozenbidict`."""

from .compat import viewitems
from ._common import BidirectionalMapping
from collections import Hashable


class frozenbidict(BidirectionalMapping, Hashable):
    """Immutable, hashable bidict type."""

    def __hash__(self):
        """Return the hash of this bidict."""
        try:
            return self._hash
        except AttributeError:
            self._hash = hash(frozenset(viewitems(self)))
            return self._hash

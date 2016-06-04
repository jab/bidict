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
        h = self._hash = hash(tuple(viewitems(self._fwd)))
        return h

"""Implements :class:`bidict.loosebidict`."""

from ._common import OVERWRITE
from ._bidict import bidict


class loosebidict(bidict):
    """A mutable bidict which uses forcing put operations by default."""

    _on_dup_val = OVERWRITE

    __setitem__ = bidict.forceput
    update = bidict.forceupdate

    def put(self, key, val, on_dup_key=OVERWRITE, on_dup_val=OVERWRITE):
        """Like :attr:`bidict.put` with default collision behavior OVERWRITE."""
        self._put(key, val, on_dup_key, on_dup_val)

"""Implements :class:`bidict.loosebidict`."""

from ._common import OVERWRITE
from ._bidict import bidict


class loosebidict(bidict):
    """A mutable bidict which uses forcing put operations by default."""

    _default_val_collision_behavior = OVERWRITE

    __setitem__ = bidict.forceput
    update = bidict.forceupdate

    def put(self, key, val, key_clbhv=OVERWRITE, val_clbhv=OVERWRITE):
        """Like :attr:`bidict.put` with default collision behavior OVERWRITE."""
        self._put(key, val, key_clbhv, val_clbhv)

"""Implements :class:`bidict.loosebidict`."""

from ._common import OVERWRITE
from ._bidict import bidict


class loosebidict(bidict):
    """A mutable bidict which uses forcing put operations by default."""

    _on_val_coll = OVERWRITE

    __setitem__ = bidict.forceput
    update = bidict.forceupdate

    def put(self, key, val, on_key_coll=OVERWRITE, on_val_coll=OVERWRITE):
        """Like :attr:`bidict.put` with default collision behavior OVERWRITE."""
        self._update(on_key_coll, on_val_coll, ((key, val),))

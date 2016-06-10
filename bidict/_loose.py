"""Implements :class:`bidict.loosebidict`."""

from ._common import OVERWRITE
from ._bidict import bidict


class loosebidict(bidict):
    """A mutable bidict which uses forcing put operations by default."""

    _on_dup_val = OVERWRITE
    _on_dup_kv = OVERWRITE
    _precheck = False

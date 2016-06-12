"""Implements :class:`bidict.loosebidict`."""

from ._common import OVERWRITE
from ._bidict import bidict


class loosebidict(bidict):
    """
    A mutable bidict with *precheck=False*
    and *OVERWRITE* duplication behaviors default.
    """

    _on_dup_val = OVERWRITE
    _on_dup_kv = OVERWRITE
    _precheck = False

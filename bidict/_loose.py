"""Implements :class:`bidict.LooseBidict`."""

from ._common import OVERWRITE
from ._bidict import bidict
from ._ordered import OrderedBidict


class LooseBidict(bidict):
    """Mutable bidict with *OVERWRITE* duplication behaviors by default."""

    _on_dup_val = OVERWRITE
    _on_dup_kv = OVERWRITE


class LooseOrderedBidict(OrderedBidict, LooseBidict):
    """Mutable ordered bidict with *OVERWRITE* duplication behaviors by default."""

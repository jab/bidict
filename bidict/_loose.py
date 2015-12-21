"""Implements :class:`bidict.loosebidict`."""

from ._bidict import bidict


class loosebidict(bidict):
    """
    A mutable bidict which always uses forcing put operations.

    Unlike :class:`bidict.bidict`,
    never raises :class:`KeyExistsException` or :class:`ValueExistsException`.
    """

    ___ = '<ignored>'

    def _put(self, key, val, overwrite_key=___, overwrite_val=___):
        return super(self.__class__, self)._put(
            key, val, overwrite_key=True, overwrite_val=True)

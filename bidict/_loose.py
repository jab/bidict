"""Implements :class:`bidict.loosebidict`."""

from ._bidict import bidict


class loosebidict(bidict):
    """A mutable bidict which uses forcing put operations by default."""

    _overwrite_key_default = True

    __setitem__ = bidict.forceput
    update = bidict.forceupdate

    def put(self, key, val, overwrite_key=True, overwrite_val=True):
        """Appease pydocstyle."""  # https://github.com/PyCQA/pydocstyle/issues/97
        self._put(key, val, overwrite_key, overwrite_val)
    put.__doc__ = bidict.put.__doc__

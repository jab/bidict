from ._common import BidirectionalMapping, _missing
from .util import pairs
from collections import MutableMapping


class bidict(BidirectionalMapping, MutableMapping):
    """
    Mutable bidirectional map type.
    """
    def _del(self, key):
        val = self._fwd[key]
        del self._fwd[key]
        del self._bwd[val]

    def __delitem__(self, key):
        self._del(key)

    __delitem__.__doc__ = dict.__delitem__.__doc__

    def __setitem__(self, key, val):
        self._put(key, val)

    __setitem__.__doc__ = dict.__setitem__.__doc__

    def put(self, key, val):
        """
        Alternative to using the setitem syntax to insert a mapping.
        """
        self._put(key, val)

    def forceput(self, key, val):
        """
        Like :attr:`bidict.bidict.put` but silently removes any existing
        mapping that would otherwise cause
        :class:`bidict.ValueExistsException` or
        :class:`bidict.CollapseException`
        before inserting the given mapping.
        """
        oldval = self._fwd.get(key, _missing)
        oldkey = self._bwd.get(val, _missing)
        if oldval is not _missing:
            del self._bwd[oldval]
        if oldkey is not _missing:
            del self._fwd[oldkey]
        self._fwd[key] = val
        self._bwd[val] = key

    def clear(self):
        self._fwd.clear()
        self._bwd.clear()

    clear.__doc__ = dict.clear.__doc__

    def pop(self, key, *args):
        val = self._fwd.pop(key, *args)
        del self._bwd[val]
        return val

    pop.__doc__ = dict.pop.__doc__

    def popitem(self):
        if not self._fwd:
            raise KeyError('popitem(): %s is empty' % self.__class__.__name__)
        key, val = self._fwd.popitem()
        del self._bwd[val]
        return key, val

    popitem.__doc__ = dict.popitem.__doc__

    def setdefault(self, key, default=None):
        val = self._fwd.setdefault(key, default)
        self._bwd[val] = key
        return val

    setdefault.__doc__ = dict.setdefault.__doc__

    def update(self, *args, **kw):
        """
        Analogous to dict.update().
        """
        return self._update(*args, **kw)

    def forceupdate(self, *args, **kw):
        """
        Equivalent to calling :attr:`bidict.bidict.forceput`
        with each of the given mappings.
        """
        for k, v in pairs(*args, **kw):
            self.forceput(k, v)

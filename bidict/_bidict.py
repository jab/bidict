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
        """
        Analogous to dict.__delitem__(), keeping bidirectionality intact.
        """
        self._del(key)

    def __setitem__(self, key, val):
        """
        Analogous to dict.__setitem__(), keeping bidirectionality intact.

        :raises ValueExistsException: if attempting to insert a mapping with a
            non-unique value.
        """
        self._put(key, val)

    def put(self, key, val):
        """
        Alternative to using :attr:`__setitem__` to insert a mapping.
        """
        self._put(key, val)

    def forceput(self, key, val):
        """
        Like :attr:`put`, but silently removes any existing
        mapping that would otherwise cause :class:`ValueExistsException`
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
        """
        Removes all items.
        """
        self._fwd.clear()
        self._bwd.clear()

    def pop(self, key, *args):
        """
        Analogous to dict.pop(), keeping bidirectionality intact.
        """
        val = self._fwd.pop(key, *args)
        del self._bwd[val]
        return val

    def popitem(self):
        """
        Analogous to dict.popitem(), keeping bidirectionality intact.
        """
        if not self._fwd:
            raise KeyError('popitem(): %s is empty' % self.__class__.__name__)
        key, val = self._fwd.popitem()
        del self._bwd[val]
        return key, val

    def setdefault(self, key, default=None):
        """
        Analogous to dict.setdefault(), keeping bidirectionality intact.
        """
        val = self._fwd.setdefault(key, default)
        self._bwd[val] = key
        return val

    def update(self, *args, **kw):
        """
        Analogous to dict.update(), keeping bidirectionality intact.
        """
        return self._update(*args, **kw)

    def forceupdate(self, *args, **kw):
        """
        Like :attr:`update`, but silently removes any existing
        mappings that would otherwise cause :class:`ValueExistsException`
        allowing key-overwriting updates to succeed.
        """
        for k, v in pairs(*args, **kw):
            self.forceput(k, v)

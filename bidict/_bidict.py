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

    def __setitem__(self, key, val):
        self._put(key, val)

    def put(self, key, val):
        """
        Alternative to using the setitem syntax to insert a mapping.
        """
        self._put(key, val)

    def forceput(self, key, val):
        """
        Like :attr:`bidict.bidict.put` but silently removes any existing
        mapping that would otherwise cause a :class:`bidict.CollapseException`
        before inserting the given mapping::

            >>> b = bidict({0: 'zero', 1: 'one'})
            >>> b.put(0, 'one')  # doctest: +IGNORE_EXCEPTION_DETAIL
            Traceback (most recent call last):
            ...
            CollapseException: ((0, 'zero'), (1, 'one'))
            >>> b.forceput(0, 'one')
            >>> b
            bidict({0: 'one'})

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

    def pop(self, key, *args):
        val = self._fwd.pop(key, *args)
        del self._bwd[val]
        return val

    def popitem(self):
        if not self._fwd:
            raise KeyError('popitem(): %s is empty' % self.__class__.__name__)
        key, val = self._fwd.popitem()
        del self._bwd[val]
        return key, val

    def setdefault(self, key, default=None):
        val = self._fwd.setdefault(key, default)
        self._bwd[val] = key
        return val

    def update(self, *args, **kw):
        for k, v in pairs(*args, **kw):
            self._put(k, v)

from ._common import BidirectionalMapping, _sentinel
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

    def __delitem__(self, keyorslice):
        if isinstance(keyorslice, slice):
            # delete by key: del b[key:]
            if self._fwd_slice(keyorslice):
                self._del(keyorslice.start)
            else:  # delete by value: del b[:val]
                self._del(self._bwd[keyorslice.stop])
        else:  # keyorslice is a key: del b[key]
            self._del(keyorslice)

    def __setitem__(self, keyorslice, keyorval):
        if isinstance(keyorslice, slice):
            # keyorslice.start is key, keyorval is val: b[key:] = val
            if self._fwd_slice(keyorslice):
                self._put(keyorslice.start, keyorval)
            else:  # keyorval is key, keyorslice.stop is val: b[:val] = key
                self._put(keyorval, keyorslice.stop)
        else:  # keyorslice is a key, keyorval is a val: b[key] = val
            self._put(keyorslice, keyorval)

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
        oldval = self._fwd.get(key, _sentinel)
        oldkey = self._bwd.get(val, _sentinel)
        if oldval is not _sentinel:
            del self._bwd[oldval]
        if oldkey is not _sentinel:
            del self._fwd[oldkey]
        self._fwd[key] = val
        self._bwd[val] = key

    def clear(self):
        self._fwd.clear()
        self._bwd.clear()

    def invert(self):
        self._fwd, self._bwd = self._bwd, self._fwd
        self._inv._fwd, self._inv._bwd = self._inv._bwd, self._inv._fwd

    def pop(self, key, *args):
        val = self._fwd.pop(key, *args)
        del self._bwd[val]
        return val

    def popitem(self):
        if not self._fwd:
            raise KeyError
        key, val = self._fwd.popitem()
        del self._bwd[val]
        return key, val

    def setdefault(self, key, default=None):
        val = self._fwd.setdefault(key, default)
        self._bwd[val] = key
        return val

    def update(self, *args, **kw):
        for k, v in pairs(*args, **kw):
            self[k] = v

from ._common import BidirectionalMapping
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
        Inserts the given mapping iff it wouldn't overwrite an existing key
        associated with the given value.

        If there is an existing value associated with the given key,
        it is silently overwritten, as with dict.

        Use :attr:`put` to guard against overwriting an existing value
        associated with the given key.

        Use :attr:`forceput` to overwrite in both cases.

        :raises ValueExistsException: if attempting to insert a mapping with a
            non-unique value.
        """
        self._put(key, val, overwrite_key=False, overwrite_val=True)

    def put(self, key, val):
        """
        Inserts the given mapping iff it wouldn't overwrite any existing
        key or value.

        :raises KeyExistsException: if attempting to insert a mapping with the
            same key as an existing mapping.

        :raises ValueExistsException: if attempting to insert a mapping with
            the same value as an existing mapping.
        """
        self._put(key, val, overwrite_key=False, overwrite_val=False)

    def forceput(self, key, val):
        """
        Silently removes any existing mappings that would be overwritten by
        the given mapping before inserting it.
        """
        self._put(key, val, overwrite_key=True, overwrite_val=True)

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

        If there is an existing value associated with the given key,
        it is silently overwritten, as with dict.

        :raises ValueExistsException: if attempting to insert a mapping with a
            non-unique value.
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

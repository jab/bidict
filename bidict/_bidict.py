"""Implements :class:`bidict.bidict`, the mutable bidirectional map type."""

from ._common import BidirectionalMapping
from .util import pairs
from collections import MutableMapping


class bidict(BidirectionalMapping, MutableMapping):
    """Mutable bidirectional map type."""

    def _del(self, key):
        val = self._fwd[key]
        del self._fwd[key]
        del self._inv[val]
        return val

    def __delitem__(self, key):
        """Like :py:meth:`dict.__delitem__`, keeping bidirectionality intact."""
        self._del(key)

    def __setitem__(self, key, val):
        """
        Set the value for *key* to *val*.

        If *key* is already associated with a different value,
        the old value will be replaced with *val*.
        Use :attr:`put` to raise an exception in this case instead.

        If *val* is already associated with a different key,
        an exception is raised
        to protect against accidentally replacing the existing mapping.

        If *key* is already associated with *val*, this is a no-op.

        Use :attr:`forceput` to unconditionally associate *key* with *val*,
        replacing any existing mappings as necessary to preserve uniqueness.

        :raises bidict.ValueExistsException: if attempting to set a mapping
            with a non-unique value.
        """
        self._put(key, val, overwrite_key=False, overwrite_val=True)

    def put(self, key, val):
        """
        Associate *key* with *val* iff *key* and *val* are both unique.

        That is, insert the given mapping iff
        *key* is not already associated with an existing value and
        *val* is not already associated with an existing key.

        If *key* is already associated with *val*, this is a no-op.

        :raises bidict.KeyExistsException: if attempting to insert a mapping
            with the same key as an existing mapping.

        :raises bidict.ValueExistsException: if attempting to insert a mapping
            with the same value as an existing mapping.
        """
        self._put(key, val, overwrite_key=False, overwrite_val=False)

    def forceput(self, key, val):
        """
        Associate *key* with *val* unconditionally.

        Replace any existing mappings containing key *key* or value *val*
        as necessary to preserve uniqueness.
        """
        self._put(key, val, overwrite_key=True, overwrite_val=True)

    def clear(self):
        """Remove all items."""
        self._fwd.clear()
        self._inv.clear()

    def pop(self, key, *args):
        """Like :py:meth:`dict.pop`, keeping bidirectionality intact."""
        ln = len(args) + 1
        if ln > 2:
            raise TypeError('pop expected at most 2 arguments, got %d' % ln)
        try:
            return self._del(key)
        except KeyError:
            if args:
                return args[0]
            raise

    def popitem(self):
        """Like :py:meth:`dict.popitem`, keeping bidirectionality intact."""
        if not self:
            raise KeyError('popitem(): %s is empty' % self.__class__.__name__)
        key, val = self._fwd.popitem()
        del self._inv[val]
        return key, val

    def setdefault(self, key, default=None):
        """Like :py:meth:`dict.setdefault`, keeping bidirectionality intact."""
        if key not in self:
            self[key] = default
        return self[key]

    def update(self, *args, **kw):
        """
        Like :py:meth:`dict.update`, keeping bidirectionality intact.

        Similar to calling :attr:`__setitem__` for each mapping given.

        :raises bidict.ValueExistsException: if attempting to insert a mapping
            with a non-unique value.
        """
        return self._update(*args, **kw)

    def forceupdate(self, *args, **kw):
        """Call :attr:`forceput` for each mapping given."""
        for k, v in pairs(*args, **kw):
            self.forceput(k, v)

"""Implements :class:`bidict.bidict`, the mutable bidirectional map type."""

from ._common import BidirectionalMapping
from .util import pairs
from collections import MutableMapping


class bidict(BidirectionalMapping, MutableMapping):
    """Mutable bidirectional map type."""

    def _del(self, key):
        val = self._fwd.pop(key)
        del self._inv[val]
        return val

    def __delitem__(self, key):
        """Like :py:meth:`dict.__delitem__`, maintaining bidirectionality."""
        self._del(key)

    def __setitem__(self, key, val):
        """
        Set the value for *key* to *val*.

        If *key* is already associated with *val*, this is a no-op.

        If *key* is already associated with a different value,
        the old value will be replaced with *val*,
        as with :py:meth:`dict.__setitem__`.
        In other words, value-overwriting modifications are allowed.

        If *val* is already associated with a different key,
        an exception is raised
        to protect against accidentally replacing the existing mapping.
        In other words, key-overwriting modifications are not allowed.

        You can use :attr:`put` instead
        if you want to specify custom key- or value-overwriting behavior,
        or use :attr:`forceput` to unconditionally associate *key* with *val*,
        replacing any existing mappings as necessary to preserve uniqueness.

        :raises bidict.ValueExistsException: if attempting to set a mapping
            with a non-unique value.
        """
        self._put(key, val, False, True)

    def put(self, key, val, overwrite_key=False, overwrite_val=False):
        """
        Associate *key* with *val* with the specified overwrite behavior.

        For example, if *overwrite_key* and *overwrite_val* are both *False*,
        then *key* will be associated with *val* if and only if
        *key* is not already associated with an existing value and
        *val* is not already associated with an existing key.

        If *key* is already associated with *val*, this is a no-op.

        :raises bidict.KeyExistsException: if attempting to insert a mapping
            with the same key as an existing mapping, and *overwrite_key* is
            *False*.

        :raises bidict.ValueExistsException: if attempting to insert a mapping
            with the same value as an existing mapping, and *overwrite_val* is
            *False*.
        """
        self._put(key, val, overwrite_key, overwrite_val)

    def forceput(self, key, val):
        """
        Associate *key* with *val* unconditionally.

        Replace any existing mappings containing key *key* or value *val*
        as necessary to preserve uniqueness.
        """
        self._put(key, val, True, True)

    def clear(self):
        """Remove all items."""
        self._fwd.clear()
        self._inv.clear()

    def pop(self, key, *args):
        """Like :py:meth:`dict.pop`, maintaining bidirectionality."""
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
        """Like :py:meth:`dict.popitem`, maintaining bidirectionality."""
        if not self:
            raise KeyError('popitem(): %s is empty' % self.__class__.__name__)
        key, val = self._fwd.popitem()
        del self._inv[val]
        return key, val

    def setdefault(self, key, default=None):
        """Like :py:meth:`dict.setdefault`, maintaining bidirectionality."""
        if key not in self:
            self[key] = default
        return self[key]

    def update(self, *args, **kw):
        """
        Like an atomic bulk :attr:`__setitem__`.

        If adding any of the items given in *args* or *kw* would cause a
        :class:`ValueExistsException <bidict.ValueExistsException>`,
        none of them will be added.

        :raises bidict.ValueExistsException: if attempting to insert a mapping
            with a non-unique value.
        """
        self._update(False, True, *args, **kw)

    def forceupdate(self, *args, **kw):
        """Like :attr:`update`, with key-overwriting ."""
        self._update(True, True, *args, **kw)

    def putall(self, overwrite_key, overwrite_val, *args, **kw):
        """
        Like an atomic bulk :attr:`put` with the specified overwrite behavior.

        If adding any of the items given in *args* or *kw* would cause a
        :class:`KeyExistsException <bidict.ValueExistsException>` or
        :class:`ValueExistsException <bidict.ValueExistsException>`,
        none of them will be added.
        """
        self._update(overwrite_key, overwrite_val, *args, **kw)

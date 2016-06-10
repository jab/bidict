"""Implements :class:`bidict.bidict`, the mutable bidirectional map type."""

from ._common import BidirectionalMapping, OVERWRITE, RAISE
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

        If *val* is already associated with a different key,
        an exception is raised
        to protect against accidental removal of the key
        that's currently associated with *val*.

        Use :attr:`put` instead if you want to specify different behavior in
        the case that the provided key or value duplicates an existing one.
        Or use :attr:`forceput` to unconditionally associate *key* with *val*,
        replacing any existing key or value as necessary to preserve uniqueness.

        :raises bidict.ValueExistsError: if *val* is not unique.
        """
        self._put(key, val, self._on_dup_key, self._on_dup_val, self._on_dup_kv)

    def put(self, key, val, on_dup_key=RAISE, on_dup_val=RAISE, on_dup_kv=RAISE):
        """
        Associate *key* with *val* with the specified duplication behaviors.

        For example, if all given duplication behaviors are
        :attr:`DuplicationBehavior.RAISE <bidict.DuplicationBehavior.RAISE>`,
        then *key* will be associated with *val* if and only if
        *key* is not already associated with an existing value and
        *val* is not already associated with an existing key,
        otherwise an exception will be raised.

        If *key* is already associated with *val*, this is a no-op.

        :raises bidict.KeyExistsError: if attempting to insert an item
            whose key duplicates an existing item's, and *on_dup_key* is
            :attr:`DuplicationBehavior.RAISE <bidict.DuplicationBehavior.RAISE>`.

        :raises bidict.ValueExistsError: if attempting to insert an item
            whose value duplicates an existing item's, and *on_dup_val* is
            :attr:`DuplicationBehavior.RAISE <bidict.DuplicationBehavior.RAISE>`.

        :raises bidict.KeyAndValueExistError: if attempting to insert an item
            whose key duplicates one existing item's, and whose value
            duplicates another existing item's, and *on_dup_kv* is
            :attr:`DuplicationBehavior.RAISE <bidict.DuplicationBehavior.RAISE>`.
        """
        self._put(key, val, on_dup_key, on_dup_val, on_dup_kv)

    def forceput(self, key, val):
        """
        Associate *key* with *val* unconditionally.

        Replace any existing mappings containing key *key* or value *val*
        as necessary to preserve uniqueness.
        """
        self._put(key, val, OVERWRITE, OVERWRITE, OVERWRITE)

    def clear(self):
        """Remove all items."""
        self._fwd.clear()
        self._inv.clear()

    def pop(self, key, *args):
        """Like :py:meth:`dict.pop`, maintaining bidirectionality."""
        l = len(args) + 1
        if l > 2:
            raise TypeError('pop expected at most 2 arguments, got %d' % l)
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
        """Like :attr:`putall` with default dup. and precheck behaviors."""
        self._update(self._on_dup_key, self._on_dup_val, self._on_dup_kv,
                     self._precheck, *args, **kw)

    def forceupdate(self, *args, **kw):
        """Like a bulk :attr:`forceput`."""
        self._update(OVERWRITE, OVERWRITE, OVERWRITE, self._precheck, *args, **kw)

    def putall(self, items, on_dup_key=RAISE, on_dup_val=RAISE, on_dup_kv=RAISE, precheck=True):
        """
        Like a bulk :attr:`put`.

        If *precheck* is truthy,
        checking for and processing duplicates
        first both within the given items
        and then between the given items and the existing items
        are both performed entirely before inserting any of the given items.

        This means that if one of the given items
        causes an exception to be raised,
        none of the items is inserted.

        Note that if there is any duplication
        that does not trigger an exception
        as per the given duplication behaviors,
        *precheck* still affects the order in which duplicates are processed
        and so affects which items are inserted, overwritten, or ignored.
        """
        self._update(on_dup_key, on_dup_val, on_dup_kv, precheck, items)

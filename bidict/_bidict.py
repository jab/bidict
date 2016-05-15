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
        the case that the provided key or value collides with an existing one.
        Or use :attr:`forceput` to unconditionally associate *key* with *val*,
        replacing any existing key or value as necessary to preserve uniqueness.

        :raises bidict.ValueExistsError: if *val* is not unique.
        """
        self._update(OVERWRITE, RAISE, False, ((key, val),))

    def put(self, key, val, on_key_coll=RAISE, on_val_coll=RAISE):
        """
        Associate *key* with *val* with the specified collision behaviors.

        For example, if *on_key_coll* and *on_val_coll* are both
        :attr:`CollisionBehavior.RAISE <bidict.CollisionBehavior.RAISE>`,
        then *key* will be associated with *val* if and only if
        *key* is not already associated with an existing value and
        *val* is not already associated with an existing key,
        otherwise an exception will be raised.

        If *key* is already associated with *val*, this is a no-op.

        :raises bidict.KeyExistsError: if attempting to insert an item
            whose key collides with an existing item's, and *on_key_coll* is
            :attr:`CollisionBehavior.RAISE <bidict.CollisionBehavior.RAISE>`.

        :raises bidict.ValueExistsError: if attempting to insert an item
            whose value collides with an existing item's, and *on_val_coll* is
            :attr:`CollisionBehavior.RAISE <bidict.CollisionBehavior.RAISE>`.
        """
        self._update(on_key_coll, on_val_coll, False, ((key, val),))

    def forceput(self, key, val):
        """
        Associate *key* with *val* unconditionally.

        Replace any existing mappings containing key *key* or value *val*
        as necessary to preserve uniqueness.
        """
        self._update(OVERWRITE, OVERWRITE, False, ((key, val),))

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
        """Like a bulk :attr:`__setitem__`. Succeeds or fails atomically."""
        self._update(OVERWRITE, RAISE, True, *args, **kw)

    def forceupdate(self, *args, **kw):
        """Like a bulk :attr:`forceput`."""
        self._update(OVERWRITE, OVERWRITE, True, *args, **kw)

    def putall(self, on_key_coll, on_val_coll, atomic, *args, **kw):
        """
        Like a bulk :attr:`put`.

        Any (k, v) item in *args* or *kw* that is already in this bidict
        will be ignored,
        regardless of specified collision behaviors.
        That is, a duplicate item will not cause an exception
        even when *on_key_coll* or *on_val_coll* is
        :attr:`CollisionBehavior.RAISE <bidict.CollisionBehavior.RAISE>`,
        since an exception is typically desired
        when only the key or only the value is not unique.

        Otherwise, if *on_key_coll* (*on_val_coll*) is
        :attr:`CollisionBehavior.RAISE <bidict.CollisionBehavior.RAISE>`,
        a :class:`bidict.KeyExistsError` (:class:`bidict.ValueExistsError`)
        will be raised if the key (value) of a given
        item duplicates that of an existing item,
        and a :class:`KeyNotUniqueError` (:class:`ValueNotUniqueError`)
        will be raised if the key (value) of a given
        item duplicates that of another given item.

        If *atomic* is True and either of the collision behaviors is *RAISE*,
        extra checking of the given items
        is done to make sure none would cause an error
        before inserting any of them.
        """
        self._update(on_key_coll, on_val_coll, atomic, *args, **kw)

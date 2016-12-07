"""Implements :class:`bidict.bidict`, the mutable bidirectional map type."""

from ._common import BidictBase, OVERWRITE, RAISE, ON_DUP_VAL
from collections import MutableMapping


class bidict(BidictBase):
    """Mutable bidirectional map type."""

    def __delitem__(self, key):
        """Like dict's :attr:`__delitem__`."""
        self._pop(key)

    def __setitem__(self, key, val):
        """
        Set the value for *key* to *val*.

        If *key* is already associated with *val*, this is a no-op.

        If *key* is already associated with a different value,
        the old value will be replaced with *val*,
        as with dict's :attr:`__setitem__`.

        If *val* is already associated with a different key,
        an exception is raised
        to protect against accidental removal of the key
        that's currently associated with *val*.

        Use :attr:`put` instead if you want to specify different behavior in
        the case that the provided key or value duplicates an existing one.
        Or use :attr:`forceput` to unconditionally associate *key* with *val*,
        replacing any existing items as necessary to preserve uniqueness.

        :raises bidict.ValueDuplicationError: if *val* duplicates that of an
            existing item.

        :raises bidict.KeyAndValueDuplicationError: if *key* duplicates the key of an
            existing item and *val* duplicates the value of a different
            existing item.
        """
        self._put(key, val, self._on_dup_key, self._on_dup_val, self._on_dup_kv)

    def put(self, key, val, on_dup_key=RAISE, on_dup_val=RAISE, on_dup_kv=ON_DUP_VAL):
        """
        Associate *key* with *val* with the specified duplication behaviors.

        For example, if all given duplication behaviors are
        :attr:`DuplicationBehavior.RAISE <bidict.DuplicationBehavior.RAISE>`,
        then *key* will be associated with *val* if and only if
        *key* is not already associated with an existing value and
        *val* is not already associated with an existing key,
        otherwise an exception will be raised.

        If *key* is already associated with *val*, this is a no-op.

        :raises bidict.KeyDuplicationError: if attempting to insert an item
            whose key duplicates an existing item's, and *on_dup_key* is
            :attr:`RAISE <bidict.DuplicationBehavior.RAISE>`.

        :raises bidict.ValueDuplicationError: if attempting to insert an item
            whose value duplicates an existing item's, and *on_dup_val* is
            :attr:`RAISE <bidict.DuplicationBehavior.RAISE>`.

        :raises bidict.KeyAndValueDuplicationError: if attempting to insert an
            item whose key duplicates one existing item's, and whose value
            duplicates another existing item's, and *on_dup_kv* is
            :attr:`RAISE <bidict.DuplicationBehavior.RAISE>`.
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
        self._clear()

    def pop(self, key, *args):
        """Like :py:meth:`dict.pop`."""
        l = len(args) + 1
        if l > 2:
            raise TypeError('pop expected at most 2 arguments, got %d' % l)
        try:
            return self._pop(key)
        except KeyError:
            if args:
                return args[0]  # default
            raise

    def popitem(self, *args, **kw):
        """Like :py:meth:`dict.popitem`."""
        if not self._fwd:
            raise KeyError('popitem(): %s is empty' % self.__class__.__name__)
        key, val = self._fwd.popitem(*args, **kw)
        del self._inv[val]
        return key, val

    def setdefault(self, key, default=None):
        """Like :py:meth:`dict.setdefault`."""
        if key not in self:
            self[key] = default
        return self[key]

    def update(self, *args, **kw):
        """
        Like :attr:`putall` with default duplication behaviors.

        In particular, for :class:`bidict.bidict`,
        *on_dup_key=OVERWRITE*, *on_dup_val=RAISE*, and *on_dup_kv=RAISE*.

        For :class:`bidict.loosebidict`,
        *on_dup_key=OVERWRITE*, *on_dup_val=OVERWRITE*, and *on_dup_kv=OVERWRITE*.
        """
        self._update(False, self._on_dup_key, self._on_dup_val, self._on_dup_kv, *args, **kw)

    def forceupdate(self, *args, **kw):
        """Like a bulk :attr:`forceput`."""
        self._update(False, OVERWRITE, OVERWRITE, OVERWRITE, *args, **kw)

    def putall(self, items, on_dup_key=RAISE, on_dup_val=RAISE, on_dup_kv=ON_DUP_VAL):
        """
        Like a bulk :attr:`put`.

        If one of the given items causes an exception to be raised,
        none of the items is inserted.
        """
        self._update(False, on_dup_key, on_dup_val, on_dup_kv, items)


# MutableMapping does not implement __subclasshook__.
# Must register as a subclass explicitly.
MutableMapping.register(bidict)

# -*- coding: utf-8 -*-
# Copyright 2017 Joshua Bronson. All Rights Reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Implements :class:`bidict.bidict`, the mutable bidirectional map type."""

from collections import MutableMapping

from ._dup import OVERWRITE, RAISE
from ._frozen import frozenbidict


class bidict(frozenbidict):  # noqa: N801; pylint: disable=invalid-name
    """Mutable bidirectional map type."""

    __hash__ = None  # since this class is mutable. explicit > implicit.

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

        Use :attr:`put` instead if you want to specify different policy in
        the case that the provided key or value duplicates an existing one.
        Or use :attr:`forceput` to unconditionally associate *key* with *val*,
        replacing any existing items as necessary to preserve uniqueness.

        :raises bidict.ValueDuplicationError: if *val* duplicates that of an
            existing item.

        :raises bidict.KeyAndValueDuplicationError: if *key* duplicates the key of an
            existing item and *val* duplicates the value of a different
            existing item.
        """
        self._put(key, val, self.on_dup_key, self.on_dup_val, self.on_dup_kv)

    def put(self, key, val, on_dup_key=RAISE, on_dup_val=RAISE, on_dup_kv=None):
        """
        Associate *key* with *val* with the specified duplication policies.

        If *on_dup_kv* is ``None``, the *on_dup_val* policy will be used for it.

        For example, if all given duplication policies are
        :attr:`RAISE <bidict.DuplicationPolicy.RAISE>`,
        then *key* will be associated with *val* if and only if
        *key* is not already associated with an existing value and
        *val* is not already associated with an existing key,
        otherwise an exception will be raised.

        If *key* is already associated with *val*, this is a no-op.

        :raises bidict.KeyDuplicationError: if attempting to insert an item
            whose key only duplicates an existing item's, and *on_dup_key* is
            :attr:`RAISE <bidict.DuplicationPolicy.RAISE>`.

        :raises bidict.ValueDuplicationError: if attempting to insert an item
            whose value only duplicates an existing item's, and *on_dup_val* is
            :attr:`RAISE <bidict.DuplicationPolicy.RAISE>`.

        :raises bidict.KeyAndValueDuplicationError: if attempting to insert an
            item whose key duplicates one existing item's, and whose value
            duplicates another existing item's, and *on_dup_kv* is
            :attr:`RAISE <bidict.DuplicationPolicy.RAISE>`.
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
        args_len = len(args) + 1
        if args_len > 2:
            raise TypeError('pop expected at most 2 arguments, got %d' % args_len)
        try:
            return self._pop(key)
        except KeyError:
            if args:
                return args[0]  # default
            raise

    def popitem(self, *args, **kw):
        """Like :py:meth:`dict.popitem`."""
        if not self:
            raise KeyError('popitem(): %s is empty' % self.__class__.__name__)
        key, val = self.fwdm.popitem(*args, **kw)
        del self.invm[val]
        return key, val

    setdefault = MutableMapping.setdefault

    def update(self, *args, **kw):
        """Like :attr:`putall` with default duplication policies."""
        if args or kw:
            self._update(False, self.on_dup_key, self.on_dup_val, self.on_dup_kv, *args, **kw)

    def forceupdate(self, *args, **kw):
        """Like a bulk :attr:`forceput`."""
        self._update(False, OVERWRITE, OVERWRITE, OVERWRITE, *args, **kw)

    def putall(self, items, on_dup_key=RAISE, on_dup_val=RAISE, on_dup_kv=None):
        """
        Like a bulk :attr:`put`.

        If one of the given items causes an exception to be raised,
        none of the items is inserted.
        """
        if items:
            self._update(False, on_dup_key, on_dup_val, on_dup_kv, items)


# MutableMapping does not implement __subclasshook__.
# Must register as a subclass explicitly.
MutableMapping.register(bidict)

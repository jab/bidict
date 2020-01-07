# -*- coding: utf-8 -*-
# Copyright 2009-2020 Joshua Bronson. All Rights Reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


#==============================================================================
#                    * Welcome to the bidict source code *
#==============================================================================

# Doing a code review? You'll find a "Code review nav" comment like the one
# below at the top and bottom of the most important source files. This provides
# a suggested initial path through the source when reviewing.
#
# Note: If you aren't reading this on https://github.com/jab/bidict, you may be
# viewing an outdated version of the code. Please head to GitHub to review the
# latest version, which contains important improvements over older versions.
#
# Thank you for reading and for any feedback you provide.

#                             * Code review nav *
#==============================================================================
#  ← Prev: _frozenbidict.py    Current: _mut.py            Next: _bidict.py →
#==============================================================================


"""Provides :class:`bidict`."""

from collections.abc import MutableMapping
from functools import wraps
from warnings import warn

from ._base import BidictBase
from ._dup import ON_DUP_RAISE, ON_DUP_DROP_OLD, OnDup
from ._sntl import _MISS


# TODO: Remove this compatibility decorator in a future release. pylint: disable=fixme
def _on_dup_compat(meth):
    deprecated = ('on_dup_key', 'on_dup_val', 'on_dup_kv')
    msg = 'The `on_dup_key`, `on_dup_val`, and `on_dup_kv` kwargs are deprecated and ' \
          'will be removed in a future version of bidict. Use the `on_dup` kwarg instead.'

    @wraps(meth)
    def wrapper(self, *args, **kw):
        shim = {s[len('on_dup_'):]: kw.pop(s) for s in deprecated if s in kw}
        if shim:
            warn(msg, stacklevel=2)
            if 'on_dup' in kw:
                raise TypeError('on_dup replaces the separate on_dup_* kwargs, do not use together')
            kw['on_dup'] = OnDup(**shim)
        return meth(self, *args, **kw)

    return wrapper


# Extend MutableMapping explicitly because it doesn't implement __subclasshook__, as well as to
# inherit method implementations it provides that we can reuse (namely `setdefault`).
class MutableBidict(BidictBase, MutableMapping):
    """Base class for mutable bidirectional mappings."""

    __slots__ = ()

    def __delitem__(self, key):
        """*x.__delitem__(y)　⟺　del x[y]*"""
        self._pop(key)

    def __setitem__(self, key, val):
        """Set the value for *key* to *val*.

        If *key* is already associated with *val*, this is a no-op.

        If *key* is already associated with a different value,
        the old value will be replaced with *val*,
        as with dict's :meth:`__setitem__`.

        If *val* is already associated with a different key,
        an exception is raised
        to protect against accidental removal of the key
        that's currently associated with *val*.

        Use :meth:`put` instead if you want to specify different behavior in
        the case that the provided key or value duplicates an existing one.
        Or use :meth:`forceput` to unconditionally associate *key* with *val*,
        replacing any existing items as necessary to preserve uniqueness.

        :raises bidict.ValueDuplicationError: if *val* duplicates that of an
            existing item.

        :raises bidict.KeyAndValueDuplicationError: if *key* duplicates the key of an
            existing item and *val* duplicates the value of a different
            existing item.
        """
        self._put(key, val, self.on_dup)

    @_on_dup_compat
    def put(self, key, val, on_dup=ON_DUP_RAISE):
        """Associate *key* with *val*, honoring the :class:`OnDup` given in *on_dup*.

        For example, if *on_dup* is :attr:`~bidict.ON_DUP_RAISE`,
        then *key* will be associated with *val* if and only if
        *key* is not already associated with an existing value and
        *val* is not already associated with an existing key,
        otherwise an exception will be raised.

        If *key* is already associated with *val*, this is a no-op.

        :raises bidict.KeyDuplicationError: if attempting to insert an item
            whose key only duplicates an existing item's, and *on_dup.key* is
            :attr:`~bidict.RAISE`.

        :raises bidict.ValueDuplicationError: if attempting to insert an item
            whose value only duplicates an existing item's, and *on_dup.val* is
            :attr:`~bidict.RAISE`.

        :raises bidict.KeyAndValueDuplicationError: if attempting to insert an
            item whose key duplicates one existing item's, and whose value
            duplicates another existing item's, and *on_dup.kv* is
            :attr:`~bidict.RAISE`.
        """
        self._put(key, val, on_dup)

    def forceput(self, key, val):
        """Associate *key* with *val* unconditionally.

        Replace any existing mappings containing key *key* or value *val*
        as necessary to preserve uniqueness.
        """
        self._put(key, val, ON_DUP_DROP_OLD)

    def clear(self):
        """Remove all items."""
        self._fwdm.clear()
        self._invm.clear()

    def pop(self, key, default=_MISS):
        """*x.pop(k[, d]) → v*

        Remove specified key and return the corresponding value.

        :raises KeyError: if *key* is not found and no *default* is provided.
        """
        try:
            return self._pop(key)
        except KeyError:
            if default is _MISS:
                raise
            return default

    def popitem(self):
        """*x.popitem() → (k, v)*

        Remove and return some item as a (key, value) pair.

        :raises KeyError: if *x* is empty.
        """
        if not self:
            raise KeyError('mapping is empty')
        key, val = self._fwdm.popitem()
        del self._invm[val]
        return key, val

    def update(self, *args, **kw):  # pylint: disable=arguments-differ
        """Like calling :meth:`putall` with *self.on_dup* passed for *on_dup*."""
        if args or kw:
            self._update(False, self.on_dup, *args, **kw)

    def forceupdate(self, *args, **kw):
        """Like a bulk :meth:`forceput`."""
        self._update(False, ON_DUP_DROP_OLD, *args, **kw)

    @_on_dup_compat
    def putall(self, items, on_dup=ON_DUP_RAISE):
        """Like a bulk :meth:`put`.

        If one of the given items causes an exception to be raised,
        none of the items is inserted.
        """
        if items:
            self._update(False, on_dup, items)


#                             * Code review nav *
#==============================================================================
#  ← Prev: _frozenbidict.py    Current: _mut.py            Next: _bidict.py →
#==============================================================================

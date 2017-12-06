# -*- coding: utf-8 -*-
# Copyright 2017 Joshua Bronson. All Rights Reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Implements :class:`frozenbidict`."""

from collections import ItemsView

from ._abc import BidirectionalMapping
from ._dup import RAISE, OVERWRITE, IGNORE
from ._exc import (
    DuplicationError, KeyDuplicationError, ValueDuplicationError, KeyAndValueDuplicationError)
from ._miss import _MISS
from .compat import PY2, _compose, iteritems
from .util import pairs


def _proxied(methodname, attrname='fwdm', doc=None):
    """Make a func that calls the indicated method on the indicated attribute."""
    def proxy(self, *args):
        """(__doc__ set dynamically below)"""
        attr = getattr(self, attrname)
        meth = getattr(attr, methodname)
        return meth(*args)
    proxy.__name__ = methodname
    proxy.__doc__ = doc or "Like dict's ``%s``." % methodname
    return proxy


# pylint: disable=invalid-name,too-many-instance-attributes
class frozenbidict(BidirectionalMapping):  # noqa: N801
    u"""
    Immutable, hashable bidict type.

    Also serves as a base class for the other bidict types.

    .. py:attribute:: fwd_cls

        The :class:`Mapping <collections.abc.Mapping>` type
        used for the backing :attr:`fwdm` mapping,
        Defaults to :class:`dict`.
        Override this if you need different behavior.

    .. py:attribute:: inv_cls

        The :class:`Mapping <collections.abc.Mapping>` type
        used for the backing :attr:`invm` mapping.
        Defaults to :class:`dict`.
        Override this if you need different behavior.

    .. py:attribute:: on_dup_key

        The default :class:`DuplicationPolicy` used in the event that an item
        duplicates only the key of another item,
        when a policy has not been specified explicitly
        (e.g. the policy used by :meth:`__setitem__` and :meth:`update`).
        Defaults to :class:`OVERWRITE <DuplicationPolicy.OVERWRITE>`
        to match :class:`dict`'s behavior.

    .. py:attribute:: on_dup_val

        The default :class:`DuplicationPolicy` used in the event that an item
        duplicates only the value of another item,
        when a policy has not been specified explicitly
        (e.g. the policy used by :meth:`__setitem__` and :meth:`update`).
        Defaults to :class:`RAISE <DuplicationPolicy.RAISE>`
        to prevent unintended overwrite of another item.

    .. py:attribute:: on_dup_kv

        The default :class:`DuplicationPolicy` used in the event that an item
        duplicates the key of another item and the value of yet another item,
        when a policy has not been specified explicitly
        (e.g. the policy used by :meth:`__setitem__` and :meth:`update`).
        Defaults to ``None``, which causes the *on_dup_kv* policy to match
        whatever *on_dup_val* policy is in effect.

    .. py:attribute:: fwdm

        The backing :class:`Mapping <collections.abc.Mapping>`
        storing the forward mapping data (*key* → *value*).

    .. py:attribute:: invm

        The backing :class:`Mapping <collections.abc.Mapping>`
        storing the inverse mapping data (*value* → *key*).

    .. py:attribute:: isinv

        :class:`bool` representing whether this bidict is the inverse of some
        other bidict which has already been created. If True, the meaning of
        :attr:`fwd_cls` and :attr:`inv_cls` is swapped. This enables
        the inverse of a bidict specifying a different :attr:`fwd_cls` and
        :attr:`inv_cls` to be passed back into its constructor such that
        the resulting copy has its :attr:`fwd_cls` and :attr:`inv_cls`
        set correctly.
    """

    on_dup_key = OVERWRITE
    on_dup_val = RAISE
    on_dup_kv = None
    fwd_cls = dict
    inv_cls = dict

    def __init__(self, *args, **kw):
        """Like dict's ``__init__``."""
        self.isinv = getattr(args[0], 'isinv', False) if args else False
        self.fwdm = self.inv_cls() if self.isinv else self.fwd_cls()
        self.invm = self.fwd_cls() if self.isinv else self.inv_cls()
        self.itemsview = ItemsView(self)
        self._init_inv()  # lgtm [py/init-calls-subclass]
        if args or kw:
            self._update(True, self.on_dup_key, self.on_dup_val, self.on_dup_kv, *args, **kw)

    def _init_inv(self):
        inv = object.__new__(self.__class__)
        inv.isinv = not self.isinv
        inv.fwd_cls = self.inv_cls
        inv.inv_cls = self.fwd_cls
        inv.fwdm = self.invm
        inv.invm = self.fwdm
        inv.itemsview = ItemsView(inv)
        inv.inv = self
        self.inv = inv

    def __repr__(self):
        tmpl = self.__class__.__name__ + '('
        if not self:
            return tmpl + ')'
        tmpl += '%r)'
        # If we have a __reversed__ method, use an ordered repr. Python doesn't provide an
        # Ordered or OrderedMapping ABC, otherwise we'd check that. (Must use getattr rather
        # than hasattr since __reversed__ may be set to None.)
        ordered = bool(getattr(self, '__reversed__', False))
        delegate = _compose(list, iteritems) if ordered else dict
        return tmpl % delegate(self)

    def __hash__(self):
        """
        Return the hash of this bidict from its contained items.

        Delegates to :meth:`compute_hash` on the first call,
        then caches the result to make future calls *O(1)*.
        """
        if getattr(self, '_hash', None) is None:  # pylint: disable=protected-access
            # pylint: disable=protected-access,attribute-defined-outside-init
            self._hash = self.itemsview._hash()
        return self._hash

    def __eq__(self, other):
        """Like :py:meth:`dict.__eq__`."""
        # This should be faster than using Mapping's __eq__ implementation.
        return self.fwdm == other

    def __ne__(self, other):
        """Like :py:meth:`dict.__eq__`."""
        # This should be faster than using Mapping's __ne__ implementation.
        return self.fwdm != other

    def _pop(self, key):
        val = self.fwdm.pop(key)
        del self.invm[val]
        return val

    def _clear(self):
        self.fwdm.clear()
        self.invm.clear()

    def _put(self, key, val, on_dup_key, on_dup_val, on_dup_kv):
        dedup_result = self._dedup_item(key, val, on_dup_key, on_dup_val, on_dup_kv)
        if dedup_result:
            self._write_item(key, val, *dedup_result)

    def _dedup_item(self, key, val, on_dup_key, on_dup_val, on_dup_kv):
        """
        Check *key* and *val* for any duplication in self.

        Handle any duplication as per the given duplication policies.

        (key, val) already present is construed as a no-op, not a duplication.

        If duplication is found and the corresponding duplication policy is
        *RAISE*, raise the appropriate error.

        If duplication is found and the corresponding duplication policy is
        *IGNORE*, return *None*.

        If duplication is found and the corresponding duplication policy is
        *OVERWRITE*, or if no duplication is found, return the dedup result
        *(isdupkey, isdupval, invbyval, fwdbykey)*.
        """
        if on_dup_kv is None:
            on_dup_kv = on_dup_val
        fwdm = self.fwdm
        invm = self.invm
        fwdbykey = fwdm.get(key, _MISS)
        invbyval = invm.get(val, _MISS)
        isdupkey = fwdbykey is not _MISS
        isdupval = invbyval is not _MISS
        if isdupkey and isdupval:
            if self._isdupitem(key, val, invbyval, fwdbykey):
                # (key, val) duplicates an existing item -> no-op.
                return
            # key and val each duplicate a different existing item.
            if on_dup_kv is RAISE:
                raise KeyAndValueDuplicationError(key, val)
            elif on_dup_kv is IGNORE:
                return
            # else on_dup_kv is OVERWRITE. Fall through to return on last line.
        elif isdupkey:
            if on_dup_key is RAISE:
                raise KeyDuplicationError(key)
            elif on_dup_key is IGNORE:
                return
            # else on_dup_key is OVERWRITE. Fall through to return on last line.
        elif isdupval:
            if on_dup_val is RAISE:
                raise ValueDuplicationError(val)
            elif on_dup_val is IGNORE:
                return
            # else on_dup_val is OVERWRITE. Fall through to return on last line.
        # else neither isdupkey nor isdupval.
        return isdupkey, isdupval, invbyval, fwdbykey

    @staticmethod
    def _isdupitem(key, val, oldkey, oldval):
        dup = oldkey == key
        assert dup == (oldval == val)
        return dup

    def _write_item(self, key, val, isdupkey, isdupval, oldkey, oldval):
        fwdm = self.fwdm
        invm = self.invm
        fwdm[key] = val
        invm[val] = key
        if isdupkey:
            del invm[oldval]
        if isdupval:
            del fwdm[oldkey]
        return key, val, isdupkey, isdupval, oldkey, oldval

    def _update(self, init, on_dup_key, on_dup_val, on_dup_kv, *args, **kw):
        if not args and not kw:
            return
        if on_dup_kv is None:
            on_dup_kv = on_dup_val
        empty = not self
        only_copy_from_bimap = empty and not kw and isinstance(args[0], BidirectionalMapping)
        if only_copy_from_bimap:  # no need to check for duplication
            write_item = self._write_item
            for (key, val) in iteritems(args[0]):
                write_item(key, val, False, False, _MISS, _MISS)
            return
        raise_on_dup = RAISE in (on_dup_key, on_dup_val, on_dup_kv)
        rollback = raise_on_dup and not init
        if rollback:
            return self._update_with_rollback(on_dup_key, on_dup_val, on_dup_kv, *args, **kw)
        _put = self._put
        for (key, val) in pairs(*args, **kw):
            _put(key, val, on_dup_key, on_dup_val, on_dup_kv)

    def _update_with_rollback(self, on_dup_key, on_dup_val, on_dup_kv, *args, **kw):
        """Update, rolling back on failure."""
        writes = []
        appendwrite = writes.append
        dedup_item = self._dedup_item
        write_item = self._write_item
        for (key, val) in pairs(*args, **kw):
            try:
                dedup_result = dedup_item(key, val, on_dup_key, on_dup_val, on_dup_kv)
            except DuplicationError:
                undo_write = self._undo_write
                for write in reversed(writes):
                    undo_write(*write)
                raise
            if dedup_result:
                write_result = write_item(key, val, *dedup_result)
                appendwrite(write_result)

    def _undo_write(self, key, val, isdupkey, isdupval, oldkey, oldval):
        if not isdupkey and not isdupval:
            self._pop(key)
            return
        fwdm = self.fwdm
        invm = self.invm
        if isdupkey:
            fwdm[key] = oldval
            invm[oldval] = key
            if not isdupval:
                del invm[val]
        if isdupval:
            invm[val] = oldkey
            fwdm[oldkey] = val
            if not isdupkey:
                del fwdm[key]

    def copy(self):
        """Like :py:meth:`dict.copy`."""
        # This should be faster than ``return self.__class__(self)``.
        copy = object.__new__(self.__class__)
        copy.isinv = self.isinv
        copy.fwdm = self.fwdm.copy()
        copy.invm = self.invm.copy()
        copy._init_inv()  # pylint: disable=protected-access
        return copy

    __copy__ = copy
    __len__ = _proxied('__len__')
    __iter__ = _proxied('__iter__')
    __getitem__ = _proxied('__getitem__')
    values = _proxied('keys', attrname='inv')
    values.__doc__ = \
        "B.values() -> a set-like object providing a view on B's values.\n\n" \
        'Note that because values of a BidirectionalMapping are also keys\n' \
        'of its inverse, this returns a *KeysView* object rather than a\n' \
        '*ValuesView* object, conferring set-alike benefits.'
    if PY2:
        viewkeys = _proxied('viewkeys')

        viewvalues = _proxied('viewkeys', attrname='inv',
                              doc=values.__doc__.replace('values()', 'viewvalues()'))
        values.__doc__ = "Like dict's ``values``."

        def viewitems(self):
            """Like dict's ``viewitems``."""
            return self.itemsview

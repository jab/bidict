# -*- coding: utf-8 -*-
# Copyright 2017 Joshua Bronson. All Rights Reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Implements :class:`frozenbidict`."""

from collections import ItemsView, KeysView

from ._abc import BidirectionalMapping
from ._clsprop import classproperty
from ._dup import RAISE, OVERWRITE, IGNORE
from ._exc import (
    DuplicationError, KeyDuplicationError, ValueDuplicationError, KeyAndValueDuplicationError)
from ._inv import InvBase, get_inv_cls
from ._miss import _MISS
from .compat import PY2, iteritems, _compose
from .util import _arg0, pairs


# pylint: disable=invalid-name,too-many-instance-attributes
class frozenbidict(BidirectionalMapping):  # noqa: N801
    """
    Immutable, hashable bidict type.

    Also serves as a base class for the other bidict types.

    .. py:attribute:: fwdm_cls

        The :class:`Mapping <collections.abc.Mapping>` type
        used for the backing :attr:`fwdm` mapping,
        Defaults to :class:`dict`.
        Override this if you need different behavior.

    .. py:attribute:: invm_cls

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
    """

    on_dup_key = OVERWRITE
    on_dup_val = RAISE
    on_dup_kv = None
    fwdm_cls = dict
    invm_cls = dict

    @classproperty
    @classmethod
    def INV_CLS(cls):  # noqa: N802
        """TODO"""
        return get_inv_cls(cls)

    def __init__(self, *args, **kw):
        """Like dict's ``__init__``."""
        self._fwdm = self.fwdm_cls()
        self._invm = self.invm_cls()
        self.inv = self.INV_CLS(self)  # pylint: disable=E1102,E1121
        if args or kw:
            self._update(True, self.on_dup_key, self.on_dup_val, self.on_dup_kv, *args, **kw)

    @property
    def fwdm(self):
        u"""
        Managed by bidict (you shouldn't need to touch this)
        but made public in case you need it.

        The backing :class:`Mapping <collections.abc.Mapping>`
        storing the forward mapping data (*key* → *value*).
        """
        return self.inv._invm  # pylint: disable=protected-access

    @property
    def invm(self):
        u"""
        Managed by bidict (you shouldn't need to touch this)
        but made public in case you need it.

        The backing :class:`Mapping <collections.abc.Mapping>`
        storing the inverse mapping data (*value* → *key*).
        """
        return self.inv._fwdm  # pylint: disable=protected-access

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

    def __eq__(self, other):
        """Like :py:meth:`dict.__eq__`."""
        # This should be faster than using Mapping.__eq__'s implementation.
        return self.fwdm == other

    def __hash__(self):
        """Return the hash of this bidict from its contained items."""
        if getattr(self, '_hash', None) is None:
            self._hash = self._itemsview()._hash()  # pylint: disable=W0201,protected-access
        return self._hash  # pylint: disable=protected-access

    def _pop(self, key):
        val = self.fwdm.pop(key)
        del self.invm[val]
        return val

    def _clear(self):
        self.fwdm.clear()
        self.invm.clear()

    def _put(self, key, val, on_dup_key, on_dup_val, on_dup_kv):
        result = self._dedup_item(key, val, on_dup_key, on_dup_val, on_dup_kv)
        if result:
            self._write_item(key, val, *result)

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

    # pylint: disable=unused-argument,no-self-use
    def _isdupitem(self, key, val, invbyval, fwdbykey):
        # invbyval is oldkey, fwdbykey is oldval.
        return key == invbyval  # implies val == fwdbkey too.

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

    def _become(self, other):
        """TODO"""
        self._clear()
        # Handle differing fwdm_cls and invm_cls correctly when other is an Inv.
        if isinstance(other, InvBase):
            # pylint: disable=protected-access
            self.inv._fwdm, self.inv._invm = self.inv._invm, self.inv._fwdm
            self._fwdm, self._invm = self._invm, self._fwdm
        fwdm = self.fwdm
        invm = self.invm
        for (key, val) in pairs(other):
            fwdm[key] = val
            invm[val] = key

    def _update(self, init, on_dup_key, on_dup_val, on_dup_kv, *args, **kw):
        if not args and not kw:
            return
        if on_dup_kv is None:
            on_dup_kv = on_dup_val
        nokw = not kw
        empty = not self
        arg0 = None
        only_become_arg0 = False
        if nokw and empty:
            arg0 = _arg0(args)
            only_become_arg0 = isinstance(arg0, (BidirectionalMapping, InvBase))
        any_raise = RAISE in (on_dup_key, on_dup_val, on_dup_kv)
        rollback = any_raise and (not only_become_arg0) and (not init)
        if rollback:
            return self._update_with_rollback(on_dup_key, on_dup_val, on_dup_kv, *args, **kw)
        if only_become_arg0:
            return self._become(arg0)
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
        cls = self.INV_CLS if isinstance(self, InvBase) else self.__class__
        return cls(self)

    __copy__ = copy

    def __iter__(self):
        """TODO"""
        return self.fwdm.__iter__()

    def __len__(self):
        """TODO"""
        return self.fwdm.__len__()

    def __getitem__(self, name):
        """TODO"""
        return self.fwdm.__getitem__(name)

    def __reduce__(self):
        """TODO"""
        cls = self.INV_CLS if isinstance(self, InvBase) else self.__class__
        return (cls, (), self.__dict__)

    def keys(self):
        """TODO"""
        return self.fwdm.keys()

    def values(self):
        u"""
        B.values() → a set-like object providing a view on B's values.

        Note that because values of a BidirectionalMapping are also keys
        of its inverse, this returns a *dict_keys* object rather than a
        *dict_values* object, thus providing the additional set APIs.
        """
        return self.invm.keys()

    def items(self):
        """TODO"""
        return self.fwdm.items()

    def _itemsview(self):
        return ItemsView(self.fwdm)

    if PY2:
        def viewvalues(self):
            """TODO"""
            return KeysView(self.invm)

        viewitems = _itemsview

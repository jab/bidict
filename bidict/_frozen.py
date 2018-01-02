# -*- coding: utf-8 -*-
# Copyright 2018 Joshua Bronson. All Rights Reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Implements :class:`frozenbidict`."""

from collections import ItemsView
from weakref import ref

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

    .. py:attribute:: on_dup_key

        The default :class:`DuplicationPolicy` used in the event that an item
        duplicates only the key of another item,
        when a policy has not been specified explicitly
        (e.g. the policy used by
        :meth:`~bidict.bidict.__setitem__` and
        :meth:`~bidict.bidict.update`).
        Defaults to :attr:`~DuplicationPolicy.OVERWRITE`
        to match :class:`dict`'s behavior.

    .. py:attribute:: on_dup_val

        The default :class:`DuplicationPolicy` used in the event that an item
        duplicates only the value of another item,
        when a policy has not been specified explicitly
        (e.g. the policy used by
        :meth:`~bidict.bidict.__setitem__` and
        :meth:`~bidict.bidict.update`).
        Defaults to :attr:`~DuplicationPolicy.RAISE`
        to prevent unintended overwrite of another item.

    .. py:attribute:: on_dup_kv

        The default :class:`DuplicationPolicy` used in the event that an item
        duplicates the key of another item and the value of yet another item,
        when a policy has not been specified explicitly
        (e.g. the policy used by
        :meth:`~bidict.bidict.__setitem__` and
        :meth:`~bidict.bidict.update`).
        Defaults to ``None``, which causes the *on_dup_kv* policy to match
        whatever *on_dup_val* policy is in effect.

    .. py:attribute:: fwdm

        The backing :class:`~collections.abc.Mapping`
        storing the forward mapping data (*key* → *value*).

    .. py:attribute:: invm

        The backing :class:`~collections.abc.Mapping`
        storing the inverse mapping data (*value* → *key*).

    .. py:attribute:: fwdm_cls

        The :class:`~collections.abc.Mapping` type
        used for the backing :attr:`fwdm` mapping,
        Defaults to :class:`dict`.
        Override this if you need different behavior.

    .. py:attribute:: invm_cls

        The :class:`~collections.abc.Mapping` type
        used for the backing :attr:`invm` mapping.
        Defaults to :class:`dict`.
        Override this if you need different behavior.
    """

    on_dup_key = OVERWRITE
    on_dup_val = RAISE
    on_dup_kv = None
    fwdm_cls = dict
    invm_cls = dict

    def __init__(self, *args, **kw):
        """Like dict's ``__init__``."""
        self.fwdm = self.fwdm_cls()
        self.invm = self.invm_cls()
        self._init_inv()  # lgtm [py/init-calls-subclass]
        if args or kw:
            self._update(True, self.on_dup_key, self.on_dup_val, self.on_dup_kv, *args, **kw)

    @classmethod
    def inv_cls(cls):
        """Return the inverse of this bidict class (with *fwdm_cls* and *invm_cls* swapped)."""
        if cls.fwdm_cls is cls.invm_cls:
            return cls
        if not getattr(cls, '_inv_cls', None):
            class _Inv(cls):
                fwdm_cls = cls.invm_cls
                invm_cls = cls.fwdm_cls
                inv_cls = cls
            _Inv.__name__ = cls.__name__
            _Inv.__doc__ = cls.__doc__
            cls._inv_cls = _Inv
        return cls._inv_cls

    def _init_inv(self):
        self._inv = inv = object.__new__(self.inv_cls())
        inv.fwdm_cls = self.invm_cls
        inv.invm_cls = self.fwdm_cls
        inv.fwdm = self.invm
        inv.invm = self.fwdm
        inv._invref = ref(self)  # pylint: disable=protected-access
        inv._inv = self._invref = None  # pylint: disable=protected-access

    @property
    def _isinv(self):
        return self._inv is None

    @property
    def inv(self):
        """The inverse of this bidict."""
        if self._inv is not None:
            return self._inv
        inv = self._invref()  # pylint: disable=E1102
        if inv is not None:
            return inv
        # Refcount of referent must have dropped to zero, as in `bidict().inv.inv`. Init a new one.
        self._init_inv()
        return self._inv

    @property
    def __dict_pickle_safe__(self):
        return dict(self.__dict__, _invref=None)

    def __reduce__(self):
        return self.__class__, (), self.__dict_pickle_safe__

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
        """Return the hash of this bidict from its contained items."""
        if getattr(self, '_hash', None) is None:  # pylint: disable=protected-access
            # pylint: disable=protected-access,attribute-defined-outside-init
            self._hash = ItemsView(self)._hash()
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
        :attr:`~bidict.DuplicationPolicy.RAISE`, raise the appropriate error.

        If duplication is found and the corresponding duplication policy is
        :attr:`~bidict.DuplicationPolicy.IGNORE`, return *None*.

        If duplication is found and the corresponding duplication policy is
        :attr:`~bidict.DuplicationPolicy.OVERWRITE`,
        or if no duplication is found,
        return the dedup result
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
        'Note that because values of a :class:`~bidict.BidirectionalMapping` are\n' \
        'also keys of its inverse, this returns a :class:`~collections.abc.KeysView`\n' \
        'rather than a :class:`~collections.abc.ValuesView`, conferring set-alike benefits.'
    if PY2:
        viewkeys = _proxied('viewkeys')

        viewvalues = _proxied('viewkeys', attrname='inv',
                              doc=values.__doc__.replace('values()', 'viewvalues()'))
        values.__doc__ = "Like dict's ``values``."

        def viewitems(self):
            """Like dict's ``viewitems``."""
            return ItemsView(self)

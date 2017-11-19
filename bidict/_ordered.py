# -*- coding: utf-8 -*-
# Copyright 2017 Joshua Bronson. All Rights Reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Implements :class:`bidict.OrderedBidict` and :class:`bidict.FrozenOrderedBidict`."""

from collections import Mapping

from ._bidict import bidict
from ._frozen import frozenbidict
from ._marker import _Marker
from ._miss import _MISS
from .compat import Reversible, iteritems, izip


_PRV = 1
_NXT = 2
_END = _Marker('END')


class FrozenOrderedBidict(frozenbidict):
    u"""
    Frozen ordered bidict. Base class for :class:`OrderedBidict`.

    .. py:attribute:: ordered_cls

        If the *other* argument in :meth:`__eq__` is an instance of this class,
        order-sensitive comparison will be performed.

    .. py:attribute:: sntl

        Managed by bidict (you shouldn't need to touch this)
        but made public since we're consenting adults.

        Sentinel node for the backing circular doubly-linked list of
        [*data*, *previous*, *next*] nodes storing the ordering.
        The *data* contained in each node is (*key_or_val*, *val_or_key*).

    .. py:attribute:: fwdm

        Managed by bidict (you shouldn't need to touch this)
        but made public since we're consenting adults.

        Backing dict storing the forward mapping data (*key* → *node*).

    .. py:attribute:: invm

        Managed by bidict (you shouldn't need to touch this)
        but made public since we're consenting adults.

        Backing dict storing the inverse mapping data (*value* → *node*).
    """

    ordered_cls = Reversible

    # Make explicit that FrozenOrderedBidict does not support overriding these:
    fwd_cls = None
    inv_cls = None

    def __init__(self, *args, **kw):
        """Like :meth:`collections.OrderedDict.__init__`."""
        # pylint: disable=super-init-not-called
        self.isinv = getattr(args[0], 'isinv', False) if args else False
        self._init_fwdm_invm()
        self._init_sntl()
        self._init_inv()
        if args or kw:
            self._update(True, self.on_dup_key, self.on_dup_val, self.on_dup_kv, *args, **kw)

    def _init_fwdm_invm(self):
        self.fwdm = getattr(self, 'fwdm', {})
        self.invm = getattr(self, 'invm', {})
        self.fwdm.clear()
        self.invm.clear()

    def _init_sntl(self):
        self.sntl = getattr(self, 'sntl', [])
        self.sntl[:] = [_END, self.sntl, self.sntl]

    def _init_inv(self):
        super(FrozenOrderedBidict, self)._init_inv()
        self.inv.sntl = self.sntl

    # Can't reuse frozenbidict.copy since we have different internal structure.
    def copy(self):
        """Like :attr:`frozenbidict.copy <bidict.frozenbidict.copy>`."""
        return self.__class__(self)

    __copy__ = copy

    def _clear(self):
        self._init_fwdm_invm()
        self._init_sntl()

    @staticmethod
    def _get_other(nodedata, key_or_val):
        first, second = nodedata
        if key_or_val == first:
            return second
        elif key_or_val == second:
            return first
        raise KeyError(key_or_val)

    def __getitem__(self, key):
        nodefwd = self.fwdm[key]
        datafwd = nodefwd[0]
        val = self._get_other(datafwd, key)
        nodeinv = self.invm[val]
        assert nodeinv is nodefwd
        return val

    def _pop(self, key):
        nodefwd = self.fwdm.pop(key)
        datafwd, prv, nxt = nodefwd
        val = self._get_other(datafwd, key)
        nodeinv = self.invm.pop(val)
        assert nodeinv is nodefwd
        prv[_NXT] = nxt
        nxt[_PRV] = prv
        del nodefwd[:]
        return val

    @staticmethod
    def _isdupitem(key, val, nodeinv, nodefwd):  # pylint: disable=arguments-differ
        """Return whether (key, val) duplicates an existing item."""
        return nodeinv is nodefwd

    # pylint: disable=arguments-differ
    def _write_item(self, key, val, isdupkey, isdupval, nodeinv, nodefwd):
        fwdm = self.fwdm
        invm = self.invm
        if not isdupkey and not isdupval:
            sntl = self.sntl
            last = sntl[_PRV]
            node = [(key, val), last, sntl]
            sntl[_PRV] = last[_NXT] = fwdm[key] = invm[val] = node
            oldkey = oldval = _MISS
        elif isdupkey and isdupval:
            datafwd = nodefwd[0]
            oldval = self._get_other(datafwd, key)
            datainv, invprv, invnxt = nodeinv
            oldkey = self._get_other(datainv, val)
            assert oldkey != key
            assert oldval != val
            # We have to collapse nodefwd and nodeinv into a single node, i.e. drop one of them.
            # Drop nodeinv, so that the item with the same key is the one overwritten in place.
            invprv[_NXT] = invnxt
            invnxt[_PRV] = invprv
            # Don't remove nodeinv's references to its neighbors since
            # if the update fails, we'll need them to undo this write.
            # Python's garbage collector should still be able to detect when
            # nodeinv is garbage and reclaim the memory.
            # Update fwdm and invm.
            tmp = fwdm.pop(oldkey)
            assert tmp is nodeinv
            tmp = invm.pop(oldval)
            assert tmp is nodefwd
            fwdm[key] = invm[val] = nodefwd
            # Update nodefwd with new item.
            nodefwd[0] = (key, val)
        elif isdupkey:
            datafwd = nodefwd[0]
            oldval = self._get_other(datafwd, key)
            oldkey = _MISS
            oldnodeinv = invm.pop(oldval)
            assert oldnodeinv is nodefwd
            invm[val] = nodefwd
            node = nodefwd
        elif isdupval:
            datainv = nodeinv[0]
            oldkey = self._get_other(datainv, val)
            oldval = _MISS
            oldnodefwd = fwdm.pop(oldkey)
            assert oldnodefwd is nodeinv
            fwdm[key] = nodeinv
            node = nodeinv
        if isdupkey ^ isdupval:
            node[0] = (key, val)
        return key, val, isdupkey, isdupval, nodeinv, nodefwd, oldkey, oldval

    # pylint: disable=arguments-differ
    def _undo_write(self, key, val, isdupkey, isdupval, nodeinv, nodefwd, oldkey, oldval):  # lgtm
        fwdm = self.fwdm
        invm = self.invm
        if not isdupkey and not isdupval:
            self._pop(key)
        elif isdupkey and isdupval:
            # datainv was never changed so should still have the original item.
            datainv, invprv, invnxt = nodeinv
            assert datainv == (val, oldkey) or datainv == (oldkey, val)
            # Restore original items.
            nodefwd[0] = (key, oldval)
            invprv[_NXT] = invnxt[_PRV] = nodeinv
            fwdm[oldkey] = invm[val] = nodeinv
            invm[oldval] = fwdm[key] = nodefwd
        elif isdupkey:
            nodefwd[0] = (key, oldval)
            tmp = invm.pop(val)
            assert tmp is nodefwd
            invm[oldval] = nodefwd
            assert fwdm[key] is nodefwd
        elif isdupval:
            nodeinv[0] = (oldkey, val)
            tmp = fwdm.pop(key)
            assert tmp is nodeinv
            fwdm[oldkey] = nodeinv
            assert invm[val] is nodeinv

    def __iter__(self, reverse=False):
        """Like :meth:`collections.OrderedDict.__iter__`."""
        fwdm = self.fwdm
        sntl = self.sntl
        cur = sntl[_PRV if reverse else _NXT]
        while cur is not sntl:
            data, prv, nxt = cur
            korv = data[0]
            node = fwdm.get(korv)
            key = korv if node is cur else data[1]
            yield key
            cur = prv if reverse else nxt

    def __reversed__(self):
        """Like :meth:`collections.OrderedDict.__reversed__`."""
        # python2 lacks `yield from` syntax
        for key in self.__iter__(reverse=True):
            yield key

    def __eq__(self, other):
        """Like :meth:`collections.OrderedDict.__eq__`."""
        if not isinstance(other, Mapping):
            return NotImplemented
        if len(self) != len(other):
            return False
        if isinstance(other, self.ordered_cls):
            return all(i == j for (i, j) in izip(iteritems(self), iteritems(other)))
        return all(self.get(k, _MISS) == v for (k, v) in iteritems(other))

    # frozenbidict.__hash__ is also correct for ordered bidicts:
    # The value is derived from all contained items and insensitive to their order.
    # If an ordered bidict "O" is equal to a mapping, its unordered counterpart "U" is too.
    # Since U1 == U2 => hash(U1) == hash(U2), then if O == U1, hash(O) must equal hash(U1).
    __hash__ = frozenbidict.__hash__  # Must set explicitly, __hash__ is never inherited.


class OrderedBidict(FrozenOrderedBidict, bidict):
    """Mutable bidict type that maintains items in insertion order."""

    __hash__ = None  # since this class is mutable. explicit > implicit.

    def popitem(self, last=True):  # pylint: disable=arguments-differ
        """Like :meth:`collections.OrderedDict.popitem`."""
        if not self:
            raise KeyError(self.__class__.__name__ + ' is empty')
        key = next((reversed if last else iter)(self))
        val = self._pop(key)
        return key, val

    def move_to_end(self, key, last=True):
        """Like :meth:`collections.OrderedDict.move_to_end`."""
        node = self.fwdm[key]
        _, prv, nxt = node
        prv[_NXT] = nxt
        nxt[_PRV] = prv
        sntl = self.sntl
        if last:
            last = sntl[_PRV]
            node[_PRV] = last
            node[_NXT] = sntl
            sntl[_PRV] = last[_NXT] = node
        else:
            frst = sntl[_NXT]
            node[_PRV] = sntl
            node[_NXT] = frst
            sntl[_NXT] = frst[_PRV] = node

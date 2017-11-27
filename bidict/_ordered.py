# -*- coding: utf-8 -*-
# Copyright 2017 Joshua Bronson. All Rights Reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Implements :class:`bidict.OrderedBidict` and :class:`bidict.FrozenOrderedBidict`."""

from collections import Mapping, ItemsView

from ._bidict import bidict
from ._clsprop import classproperty
from ._frozen import frozenbidict
from ._marker import _Marker
from ._miss import _MISS
from .compat import PY2, iteritems, izip
from .util import pairs


_PRV = 1
_NXT = 2
_END = _Marker('END')


class FrozenOrderedBidict(frozenbidict):
    """Frozen ordered bidict. Base class for :class:`OrderedBidict`."""

    @classproperty
    @staticmethod
    def fwdm_cls():
        """Does not support overriding."""
        return dict

    @classproperty
    @staticmethod
    def invm_cls():
        """Does not support overriding."""
        return dict

    def __init__(self, *args, **kw):
        """Like :meth:`collections.OrderedDict.__init__`."""
        self._sntl = _make_sentinel()
        super(FrozenOrderedBidict, self).__init__(*args, **kw)

    @property
    def sntl(self):
        """TODO"""
        return self.inv._sntl  # pylint: disable=protected-access

    def _clear(self):
        self.fwdm.clear()
        self.invm.clear()
        self.sntl[:] = [_END, self.sntl, self.sntl]

    def _become(self, other):
        """TODO"""
        self._clear()
        fwdm = self.fwdm
        invm = self.invm
        sntl = self.sntl
        cur = sntl
        nxt = sntl[_NXT]
        for (key, val) in pairs(other):
            nxt = [(key, val), cur, sntl]
            cur[_NXT] = fwdm[key] = invm[val] = nxt
            cur = nxt
        sntl[_PRV] = nxt

    def __getitem__(self, key):
        fwdm = self.fwdm
        nodefwd = fwdm[key]
        datafwd = nodefwd[0]
        val = _get_other(datafwd, key)
        return val

    def _pop(self, key):
        fwdm = self.fwdm
        invm = self.invm
        nodefwd = fwdm.pop(key)
        datafwd, prv, nxt = nodefwd
        val = _get_other(datafwd, key)
        del invm[val]
        prv[_NXT] = nxt
        nxt[_PRV] = prv
        del nodefwd[:]
        return val

    def _isdupitem(self, key, val, invbyval, fwdbykey):  # pylint: disable=unused-argument
        """Return whether (key, val) duplicates an existing item."""
        # invbyval is nodefwd, fwdbykey is nodeinv.
        return invbyval is fwdbykey

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
            oldval = _get_other(datafwd, key)
            datainv, invprv, invnxt = nodeinv
            oldkey = _get_other(datainv, val)
            # We have to collapse nodefwd and nodeinv into a single node, i.e. drop one of them.
            # Drop nodeinv, so that the item with the same key is the one overwritten in place.
            invprv[_NXT] = invnxt
            invnxt[_PRV] = invprv
            # Don't remove nodeinv's references to its neighbors since
            # if the update fails, we'll need them to undo this write.
            # Python's garbage collector should still be able to detect when
            # nodeinv is garbage and reclaim the memory.
            # Update fwdm and invm.
            del fwdm[oldkey]
            del invm[oldval]
            fwdm[key] = invm[val] = nodefwd
            # Update nodefwd with new item.
            nodefwd[0] = (key, val)
        elif isdupkey:
            datafwd = nodefwd[0]
            oldval = _get_other(datafwd, key)
            oldkey = _MISS
            del invm[oldval]
            invm[val] = nodefwd
            node = nodefwd
        elif isdupval:
            datainv = nodeinv[0]
            oldkey = _get_other(datainv, val)
            oldval = _MISS
            del fwdm[oldkey]
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
            _, invprv, invnxt = nodeinv
            # Restore original items.
            nodefwd[0] = (key, oldval)
            invprv[_NXT] = invnxt[_PRV] = nodeinv
            fwdm[oldkey] = invm[val] = nodeinv
            invm[oldval] = fwdm[key] = nodefwd
        elif isdupkey:
            nodefwd[0] = (key, oldval)
            del invm[val]
            invm[oldval] = nodefwd
        elif isdupval:
            nodeinv[0] = (oldkey, val)
            del fwdm[key]
            fwdm[oldkey] = nodeinv

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
        # Python 2 lacks `yield from` syntax
        for key in self.__iter__(reverse=True):
            yield key

    def __eq__(self, other, order_sensitive=False):
        """Check for equality with ``other`` as per ``order_sensitive``."""
        if not isinstance(other, Mapping):
            return NotImplemented
        if len(self) != len(other):
            return False
        if order_sensitive:
            return all(i == j for (i, j) in izip(iteritems(self), iteritems(other)))
        return all(self.get(k, _MISS) == v for (k, v) in iteritems(other))

    def equals_order_sensitive(self, other):
        """Check equality with other with order sensitivity."""
        return self.__eq__(other, order_sensitive=True)

    # frozenbidict.__hash__ is also correct for ordered bidicts:
    # The value is derived from all contained items and insensitive to their order.
    # If an ordered bidict "O" is equal to a mapping, its unordered counterpart "U" is too.
    # Since U1 == U2 => hash(U1) == hash(U2), then if O == U1, hash(O) must equal hash(U1).
    __hash__ = frozenbidict.__hash__  # Must set explicitly, __hash__ is never inherited.

    def _itemsview(self):
        return ItemsView(self)

    if PY2:
        viewitems = _itemsview

        def items(self):
            """TODO"""
            return list(izip(self.fwdm, self.invm))

    else:
        items = _itemsview


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
        fwdm = self.fwdm
        node = fwdm[key]
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


def _make_sentinel():
    sntl = []
    sntl[:] = [_END, sntl, sntl]
    return sntl


def _get_other(nodedata, key_or_val):
    first, second = nodedata
    if key_or_val == first:
        return second
    return first

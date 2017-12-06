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
from .compat import iteritems, izip


_PRV = 1
_NXT = 2
_END = _Marker('END')


class FrozenOrderedBidict(frozenbidict):
    u"""
    Frozen ordered bidict. Base class for :class:`OrderedBidict`.

    .. py:attribute:: sntl

        Sentinel node for the backing circular doubly-linked list of
        [*data*, *previous*, *next*] nodes storing the ordering.
        The *data* contained in each node is (*key_or_val*, *val_or_key*).

    .. py:attribute:: fwdm

        Backing dict storing the forward mapping data (*key* → *node*).

    .. py:attribute:: invm

        Backing dict storing the inverse mapping data (*value* → *node*).
    """

    def __init__(self, *args, **kw):
        """Like :meth:`collections.OrderedDict.__init__`."""
        self.sntl = _make_sentinel()
        super(FrozenOrderedBidict, self).__init__(*args, **kw)

    def _init_inv(self):
        super(FrozenOrderedBidict, self)._init_inv()
        self.inv.sntl = self.sntl

    # Can't reuse frozenbidict.copy since we have different internal structure.
    def copy(self):
        """Like :meth:`collections.OrderedDict.copy`."""
        # This should be faster than ``return self.__class__(self)``.
        copy = object.__new__(self.__class__)
        copy.isinv = self.isinv
        sntl = _make_sentinel()
        fwdm = {}
        invm = {}
        cur = sntl
        nxt = sntl[_NXT]
        for (key, val) in iteritems(self):
            nxt = [(key, val), cur, sntl]
            cur[_NXT] = fwdm[key] = invm[val] = nxt
            cur = nxt
        sntl[_PRV] = nxt
        copy.sntl = sntl
        copy.fwdm = fwdm
        copy.invm = invm
        copy._init_inv()  # pylint: disable=protected-access
        return copy

    __copy__ = copy

    def _clear(self):
        self.fwdm.clear()
        self.invm.clear()
        self.sntl[:] = [_END, self.sntl, self.sntl]

    def __getitem__(self, key):
        nodefwd = self.fwdm[key]
        datafwd = nodefwd[0]
        val = _get_other(datafwd, key)
        nodeinv = self.invm[val]
        assert nodeinv is nodefwd
        return val

    def _pop(self, key):
        nodefwd = self.fwdm.pop(key)
        datafwd, prv, nxt = nodefwd
        val = _get_other(datafwd, key)
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
            oldval = _get_other(datafwd, key)
            datainv, invprv, invnxt = nodeinv
            oldkey = _get_other(datainv, val)
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
            oldval = _get_other(datafwd, key)
            oldkey = _MISS
            oldnodeinv = invm.pop(oldval)
            assert oldnodeinv is nodefwd
            invm[val] = nodefwd
            node = nodefwd
        elif isdupval:
            datainv = nodeinv[0]
            oldkey = _get_other(datainv, val)
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
        for key in self.__iter__(reverse=True):
            yield key

    def __ne__(self, other, order_sensitive=False):
        result = self.__eq__(other, order_sensitive=order_sensitive)
        if result is NotImplemented:
            return NotImplemented
        assert isinstance(result, bool)
        return not result

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


def _make_sentinel():
    sntl = []
    sntl[:] = [_END, sntl, sntl]
    return sntl


def _get_other(nodedata, key_or_val):
    first, second = nodedata
    if key_or_val == first:
        return second
    assert key_or_val == second
    return first

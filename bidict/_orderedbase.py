# -*- coding: utf-8 -*-
# Copyright 2018 Joshua Bronson. All Rights Reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


#==============================================================================
#                    * Welcome to the bidict source code *
#==============================================================================

# Doing a code review? You'll find a "Code review nav" comment like the one
# below at the top and bottom of the most important source files. This provides
# a suggested path through the source while you're still getting familiar.
#
# Note: If you aren't reading this on https://github.com/jab/bidict, you may be
# viewing an outdated version of the code. Please head to GitHub to review the
# latest version, which contains important improvements over older versions.
#
# Thank you for reading and for any feedback you provide.

#                             * Code review nav *
#==============================================================================
#  ← Prev: _bidict.py       Current: _orderedbase.py  Next: _frozenordered.py →
#==============================================================================


"""Provides :class:`OrderedBidictBase`."""

from ._base import _WriteResult, BidictBase
from ._marker import _Marker
from ._miss import _MISS
from .compat import iteritems, zip, Mapping  # pylint: disable=redefined-builtin


_DAT = 0
_PRV = 1
_NXT = 2
_END = _Marker('END')


class OrderedBidictBase(BidictBase):  # lgtm [py/missing-equals]
    """Base class implementing an ordered :class:`BidirectionalMapping`."""

    __slots__ = ('_sntl',)

    def __init__(self, *args, **kw):
        """Make a new ordered bidirectional mapping.
        The signature is the same as that of regular dictionaries.
        Items passed in are added in the order they are passed,
        respecting this bidict type's duplication policies along the way.
        The order in which items are inserted is remembered,
        similar to :class:`collections.OrderedDict`.
        """
        # Sentinel node for the backing linked list that stores the items in order.
        # Implemented as a circular doubly-linked list.
        # A linked list node (including the sentinel node) is represented
        # via a 3-element list, `[data, prev_node, next_node]`, for efficiency
        # (hence the constant `_PRV` and `_NXT` indices above).
        # `data` is a pair containing the key and value of an item
        # in an arbitrary order, i.e. (`key_or_val`, `val_or_key`).
        self._sntl = _make_sentinel()

        # Like unordered bidicts, ordered bidicts also store
        # two backing one-directional mappings `fwdm` and `invm`.
        # But rather than mapping key→val and val→key (respectively),
        # they map key→node and val→node (respectively),
        # where the node is the same when key and val are associated with one another.
        # To effect this difference, _write_item and _undo_write are overridden.
        # But much of the rest of BidictBase's implementation,
        # including BidictBase.__init__ and BidictBase._update,
        # are inherited and reused without modification. Code reuse ftw.
        super(OrderedBidictBase, self).__init__(*args, **kw)

    def _init_inv(self):
        super(OrderedBidictBase, self)._init_inv()
        self.inv._sntl = self._sntl  # pylint: disable=protected-access

    # Can't reuse BidictBase.copy since ordered bidicts have different internal structure.
    def copy(self):
        """A shallow copy of this ordered bidict."""
        # Fast copy implementation bypassing __init__. See comments in :meth:`BidictBase.copy`.
        copy = object.__new__(self.__class__)
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
        copy._sntl = sntl  # pylint: disable=protected-access
        copy._fwdm = fwdm  # pylint: disable=protected-access
        copy._invm = invm  # pylint: disable=protected-access
        copy._init_inv()  # pylint: disable=protected-access
        return copy

    def __getitem__(self, key):
        nodefwd = self._fwdm[key]
        datafwd = nodefwd[_DAT]
        val = _get_other(datafwd, key)
        nodeinv = self._invm[val]
        assert nodeinv is nodefwd
        return val

    def _pop(self, key):
        nodefwd = self._fwdm.pop(key)
        datafwd, prv, nxt = nodefwd
        val = _get_other(datafwd, key)
        nodeinv = self._invm.pop(val)
        assert nodeinv is nodefwd
        prv[_NXT] = nxt
        nxt[_PRV] = prv
        del nodefwd[:]
        return val

    @staticmethod
    def _isdupitem(key, val, dedup_result):
        """Return whether (key, val) duplicates an existing item."""
        isdupkey, isdupval, nodeinv, nodefwd = dedup_result
        isdupitem = nodeinv is nodefwd
        if isdupitem:
            assert isdupkey
            assert isdupval
            data = nodefwd[_DAT]
            assert key in data
            assert val in data
        return isdupitem

    def _write_item(self, key, val, dedup_result):  # pylint: disable=too-many-locals
        fwdm = self._fwdm
        invm = self._invm
        isdupkey, isdupval, nodeinv, nodefwd = dedup_result
        if not isdupkey and not isdupval:
            sntl = self._sntl
            last = sntl[_PRV]
            node = [(key, val), last, sntl]
            sntl[_PRV] = last[_NXT] = fwdm[key] = invm[val] = node
            oldkey = oldval = _MISS
        elif isdupkey and isdupval:
            datafwd = nodefwd[_DAT]
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
            nodefwd[_DAT] = (key, val)
        elif isdupkey:
            datafwd = nodefwd[_DAT]
            oldval = _get_other(datafwd, key)
            oldkey = _MISS
            oldnodeinv = invm.pop(oldval)
            assert oldnodeinv is nodefwd
            invm[val] = nodefwd
            node = nodefwd
        else:  # isdupval
            datainv = nodeinv[_DAT]
            oldkey = _get_other(datainv, val)
            oldval = _MISS
            oldnodefwd = fwdm.pop(oldkey)
            assert oldnodefwd is nodeinv
            fwdm[key] = nodeinv
            node = nodeinv
        if isdupkey ^ isdupval:
            node[_DAT] = (key, val)
        return _WriteResult(key, val, oldkey, oldval)

    def _undo_write(self, dedup_result, write_result):  # pylint: disable=too-many-locals
        fwdm = self._fwdm
        invm = self._invm
        isdupkey, isdupval, nodeinv, nodefwd = dedup_result
        key, val, oldkey, oldval = write_result
        if not isdupkey and not isdupval:
            self._pop(key)
        elif isdupkey and isdupval:
            # datainv was never changed so should still have the original item.
            datainv, invprv, invnxt = nodeinv
            assert datainv == (val, oldkey) or datainv == (oldkey, val)
            # Restore original items.
            nodefwd[_DAT] = (key, oldval)
            invprv[_NXT] = invnxt[_PRV] = nodeinv
            fwdm[oldkey] = invm[val] = nodeinv
            invm[oldval] = fwdm[key] = nodefwd
        elif isdupkey:
            nodefwd[_DAT] = (key, oldval)
            tmp = invm.pop(val)
            assert tmp is nodefwd
            invm[oldval] = nodefwd
            assert fwdm[key] is nodefwd
        else:  # isdupval
            nodeinv[_DAT] = (oldkey, val)
            tmp = fwdm.pop(key)
            assert tmp is nodeinv
            fwdm[oldkey] = nodeinv
            assert invm[val] is nodeinv

    def __iter__(self, reverse=False):
        """An iterator over this bidict's items in order."""
        fwdm = self._fwdm
        sntl = self._sntl
        nextidx = _PRV if reverse else _NXT
        cur = sntl[nextidx]
        while cur is not sntl:  # lgtm [py/comparison-using-is]
            data = cur[_DAT]
            korv = data[0]
            node = fwdm.get(korv)
            key = korv if node is cur else data[1]
            yield key
            cur = cur[nextidx]

    def __reversed__(self):
        """An iterator over this bidict's items in reverse order."""
        for key in self.__iter__(reverse=True):
            yield key

    def equals_order_sensitive(self, other):
        """Order-sensitive equality check.

        See also :ref:`eq-order-insensitive`
        """
        if not isinstance(other, Mapping) or len(self) != len(other):
            return False
        return all(i == j for (i, j) in zip(iteritems(self), iteritems(other)))

    def __repr_delegate__(self):
        """See :meth:`bidict.BidictBase.__repr_delegate__`."""
        return list(iteritems(self))


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


#                             * Code review nav *
#==============================================================================
#  ← Prev: _bidict.py       Current: _orderedbase.py  Next: _frozenordered.py →
#==============================================================================

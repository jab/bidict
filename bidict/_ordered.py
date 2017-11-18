# -*- coding: utf-8 -*-
# Copyright 2017 Joshua Bronson. All Rights Reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Implements :class:`bidict.OrderedBidict` and :class:`bidict.FrozenOrderedBidict`."""

from collections import Mapping

from ._common import _Marker, _MISS
from ._base import frozenbidict
from ._bidict import bidict
from .compat import Reversible, iteritems, izip


_PRV = 1
_NXT = 2
_END = _Marker('END')


class FrozenOrderedBidict(frozenbidict):
    """
    Frozen ordered bidict. Base class for :class:`OrderedBidict`.

    .. py:attribute:: ORDERED_CLS

        If the *other* argument in :meth:`__eq__` is an instance of this class,
        order-sensitive comparison will be performed.
    """

    ORDERED_CLS = Reversible

    def __init__(self, *args, **kw):
        """Like :meth:`collections.OrderedDict.__init__`."""
        # pylint: disable=super-init-not-called
        self._isinv = getattr(args[0], '_isinv', False) if args else False
        self._end = []  # circular doubly-linked list of [{key: val, val: key}, prv, nxt] nodes
        self._init_end()
        self._fwd = {}  # key -> node. _fwd_class ignored.
        self._inv = {}  # val -> node. _inv_class ignored.
        self._init_inv()
        if args or kw:
            self._update(True, self._on_dup_key, self._on_dup_val, self._on_dup_kv, *args, **kw)

    def _init_end(self):
        end = self._end
        end += [_END, end, end]  # sentinel node for doubly linked list

    def _init_inv(self):
        super(FrozenOrderedBidict, self)._init_inv()
        # pylint: disable=protected-access
        self.inv._end = self._end

    # Must override frozenbidict.copy since we have different internal structure.
    def copy(self):
        """Like :attr:`frozenbidict.copy <bidict.frozenbidict.copy>`."""
        return self.__class__(self)

    __copy__ = copy

    def _clear(self):
        super(FrozenOrderedBidict, self)._clear()
        del self._end[:]
        self._init_end()

    def __getitem__(self, key):
        node = self._fwd[key]
        data = node[0]
        return data[key]

    def _pop(self, key):
        nodefwd = self._fwd.pop(key)
        data, prv, nxt = nodefwd
        val = data[key]
        nodeinv = self._inv.pop(val)
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
        fwd = self._fwd
        inv = self._inv
        if not isdupkey and not isdupval:
            end = self._end
            lst = end[_PRV]
            node = [{key: val, val: key}, lst, end]
            end[_PRV] = lst[_NXT] = fwd[key] = inv[val] = node
            oldkey = oldval = _MISS
        elif isdupkey and isdupval:
            fwdd, _, _ = nodefwd
            oldval = fwdd[key]
            invd, invprv, invnxt = nodeinv
            oldkey = invd[val]
            assert oldkey != key
            assert oldval != val
            # We have to collapse nodefwd and nodeinv into a single node.
            # Drop nodeinv so that item with same key overwritten in place.
            invprv[_NXT] = invnxt
            invnxt[_PRV] = invprv
            # Don't remove nodeinv's references to its neighbors since
            # if the update fails, we'll need them to undo this write.
            # Python's garbage collector should still be able to detect when
            # nodeinv is garbage and reclaim the memory.
            # Update fwd and inv.
            tmp = fwd.pop(oldkey)
            assert tmp is nodeinv
            tmp = inv.pop(oldval)
            assert tmp is nodefwd
            fwd[key] = inv[val] = nodefwd
            # Update nodefwd with new item.
            fwdd.clear()
            fwdd[key] = val
            fwdd[val] = key
        elif isdupkey:
            data = nodefwd[0]
            oldval = data[key]
            oldkey = _MISS
            oldnodeinv = inv.pop(oldval)
            assert oldnodeinv is nodefwd
            inv[val] = nodefwd
        elif isdupval:
            data = nodeinv[0]
            oldkey = data[val]
            oldval = _MISS
            oldnodefwd = fwd.pop(oldkey)
            assert oldnodefwd is nodeinv
            fwd[key] = nodeinv
        if isdupkey ^ isdupval:
            data.clear()
            data[key] = val
            data[val] = key
        return key, val, isdupkey, isdupval, nodeinv, nodefwd, oldkey, oldval

    # pylint: disable=arguments-differ
    def _undo_write(self, key, val, isdupkey, isdupval, nodeinv, nodefwd, oldkey, oldval):  # lgtm
        fwd = self._fwd
        inv = self._inv
        if not isdupkey and not isdupval:
            self._pop(key)
        elif isdupkey and isdupval:
            fwdd, _, _ = nodefwd
            invd, invprv, invnxt = nodeinv
            # Restore original items.
            fwdd.clear()
            fwdd[key] = oldval
            fwdd[oldval] = key
            # invd was never changed so should still have the original item.
            expectinvd = {oldkey: val, val: oldkey}
            assert invd == expectinvd
            # Undo replacing nodeinv with nodefwd.
            invprv[_NXT] = invnxt[_PRV] = nodeinv
            fwd[oldkey] = inv[val] = nodeinv
            inv[oldval] = fwd[key] = nodefwd
        elif isdupkey:
            data = nodefwd[0]
            data.clear()
            data[key] = oldval
            data[oldval] = key
            tmp = inv.pop(val)
            assert tmp is nodefwd
            inv[oldval] = nodefwd
            assert fwd[key] is nodefwd
        elif isdupval:
            data = nodeinv[0]
            data.clear()
            data[oldkey] = val
            data[val] = oldkey
            tmp = fwd.pop(key)
            assert tmp is nodeinv
            fwd[oldkey] = nodeinv
            assert inv[val] is nodeinv

    def __iter__(self, reverse=False):
        """Like :meth:`collections.OrderedDict.__iter__`."""
        fwd = self._fwd
        end = self._end
        cur = end[_PRV if reverse else _NXT]
        while cur is not end:
            data, prv, nxt = cur
            korv = next(iter(data))  # lgtm [py/unguarded-next-in-generator]
            node = fwd.get(korv)
            key = korv if node is cur else data[korv]
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
        if isinstance(other, self.ORDERED_CLS):
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
        node = self._fwd[key]
        _, prv, nxt = node
        prv[_NXT] = nxt
        nxt[_PRV] = prv
        end = self._end
        if last:
            lst = end[_PRV]
            node[_PRV] = lst
            node[_NXT] = end
            end[_PRV] = lst[_NXT] = node
        else:
            fst = end[_NXT]
            node[_PRV] = end
            node[_NXT] = fst
            end[_NXT] = fst[_PRV] = node

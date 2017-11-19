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
    """
    Frozen ordered bidict. Base class for :class:`OrderedBidict`.

    .. py:attribute:: ordered_cls

        If the *other* argument in :meth:`__eq__` is an instance of this class,
        order-sensitive comparison will be performed.

    .. py:attribute:: end

        Managed by bidict (you shouldn't need to touch this)
        but made public since we're consenting adults.

        Backing circular doubly-linked list of [*data*, *previous*, *next*] nodes,
        where *data* is {key: val, val: key}.

    .. py:attribute:: fwdm

        Managed by bidict (you shouldn't need to touch this)
        but made public since we're consenting adults.

        Backing dict storing the forward mapping data (key → node).

        # circular doubly-linked list of [data, prv, nxt] nodes

    .. py:attribute:: fwdm

        Managed by bidict (you shouldn't need to touch this)
        but made public since we're consenting adults.

        Backing dict storing the forward mapping data (key → node).

    .. py:attribute:: invm

        Managed by bidict (you shouldn't need to touch this)
        but made public since we're consenting adults.

        Backing dict storing the inverse mapping data (value → node).
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
        self._init_end()
        self._init_inv()
        if args or kw:
            self._update(True, self.on_dup_key, self.on_dup_val, self.on_dup_kv, *args, **kw)

    def _init_fwdm_invm(self):
        self.fwdm = getattr(self, 'fwdm', {})
        self.invm = getattr(self, 'invm', {})
        self.fwdm.clear()
        self.invm.clear()

    def _init_end(self):
        self.end = getattr(self, 'end', [])
        self.end.clear()
        self.end += [_END, self.end, self.end]  # sentinel node for doubly linked list

    def _init_inv(self):
        super(FrozenOrderedBidict, self)._init_inv()
        self.inv.end = self.end

    # Can't reuse frozenbidict.copy since we have different internal structure.
    def copy(self):
        """Like :attr:`frozenbidict.copy <bidict.frozenbidict.copy>`."""
        return self.__class__(self)

    __copy__ = copy

    def _clear(self):
        self._init_fwdm_invm()
        self._init_end()

    def __getitem__(self, key):
        node = self.fwdm[key]
        data = node[0]
        return data[key]

    def _pop(self, key):
        nodefwd = self.fwdm.pop(key)
        data, prv, nxt = nodefwd
        val = data[key]
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
            end = self.end
            lst = end[_PRV]
            node = [{key: val, val: key}, lst, end]
            end[_PRV] = lst[_NXT] = fwdm[key] = invm[val] = node
            oldkey = oldval = _MISS
        elif isdupkey and isdupval:
            fwddata, _, _ = nodefwd
            oldval = fwddata[key]
            invdata, invprv, invnxt = nodeinv
            oldkey = invdata[val]
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
            # Update fwdm and invm.
            tmp = fwdm.pop(oldkey)
            assert tmp is nodeinv
            tmp = invm.pop(oldval)
            assert tmp is nodefwd
            fwdm[key] = invm[val] = nodefwd
            # Update nodefwd with new item.
            fwddata.clear()
            fwddata[key] = val
            fwddata[val] = key
        elif isdupkey:
            fwddata = nodefwd[0]
            oldval = fwddata[key]
            oldkey = _MISS
            oldnodeinv = invm.pop(oldval)
            assert oldnodeinv is nodefwd
            invm[val] = nodefwd
        elif isdupval:
            fwddata = nodeinv[0]
            oldkey = fwddata[val]
            oldval = _MISS
            oldnodefwd = fwdm.pop(oldkey)
            assert oldnodefwd is nodeinv
            fwdm[key] = nodeinv
        if isdupkey ^ isdupval:
            fwddata.clear()
            fwddata[key] = val
            fwddata[val] = key
        return key, val, isdupkey, isdupval, nodeinv, nodefwd, oldkey, oldval

    # pylint: disable=arguments-differ
    def _undo_write(self, key, val, isdupkey, isdupval, nodeinv, nodefwd, oldkey, oldval):  # lgtm
        fwdm = self.fwdm
        invm = self.invm
        if not isdupkey and not isdupval:
            self._pop(key)
        elif isdupkey and isdupval:
            fwddata, _, _ = nodefwd
            invdata, invprv, invnxt = nodeinv
            # Restore original items.
            fwddata.clear()
            fwddata[key] = oldval
            fwddata[oldval] = key
            # invdata was never changed so should still have the original item.
            tmp = {oldkey: val, val: oldkey}
            assert invdata == tmp
            # Undo replacing nodeinv with nodefwd.
            invprv[_NXT] = invnxt[_PRV] = nodeinv
            fwdm[oldkey] = invm[val] = nodeinv
            invm[oldval] = fwdm[key] = nodefwd
        elif isdupkey:
            fwddata = nodefwd[0]
            fwddata.clear()
            fwddata[key] = oldval
            fwddata[oldval] = key
            tmp = invm.pop(val)
            assert tmp is nodefwd
            invm[oldval] = nodefwd
            assert fwdm[key] is nodefwd
        elif isdupval:
            invdata = nodeinv[0]
            invdata.clear()
            invdata[oldkey] = val
            invdata[val] = oldkey
            tmp = fwdm.pop(key)
            assert tmp is nodeinv
            fwdm[oldkey] = nodeinv
            assert invm[val] is nodeinv

    def __iter__(self, reverse=False):
        """Like :meth:`collections.OrderedDict.__iter__`."""
        fwdm = self.fwdm
        end = self.end
        cur = end[_PRV if reverse else _NXT]
        while cur is not end:
            data, prv, nxt = cur
            korv = next(iter(data))  # lgtm [py/unguarded-next-in-generator]
            node = fwdm.get(korv)
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
        end = self.end
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

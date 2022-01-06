# Copyright 2009-2022 Joshua Bronson. All Rights Reserved.
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
# ← Prev: _bidict.py       Current: _orderedbase.py   Next: _frozenordered.py →
#==============================================================================


"""Provide :class:`OrderedBidictBase`."""

import typing as _t
import weakref
from copy import copy

from ._abc import MutableBidirectionalMapping
from ._base import _NONE, _DedupResult, _WriteResult, BidictBase, BT
from ._bidict import bidict
from ._typing import KT, VT, OKT, OVT, IterItems, MapOrIterItems, KeysView, ItemsView


class _WeakAttr:
    def __init__(self, *, slot: str) -> None:
        self.slot = slot

    def __set__(self, instance: _t.Any, value: _t.Any) -> None:
        setattr(instance, self.slot, weakref.ref(value))

    def __get__(self, instance: _t.Any, owner: _t.Any) -> _t.Any:
        return getattr(instance, self.slot)()


class _Node:
    """A node in a circular doubly-linked list
    used to encode the order of items in an ordered bidict.

    A weak reference to the previous node is stored
    to avoid creating strong reference cycles.
    Managing the weak reference is handled automatically by _WeakAttr.

    Because an ordered bidict retains two strong references
    to each node instance (one from its backing `_fwdm` mapping
    and one from its `_invm` mapping), a node's refcount will not
    drop to zero (and so will not be garbage collected) as long as
    the ordered bidict that contains it is still alive.
    Because nodes don't have strong reference cycles,
    once their containing bidict is freed,
    they too are immediately freed.
    """

    prv: '_Node' = _WeakAttr(slot='_prv_weak')  # type: ignore[assignment]
    __slots__ = ('_prv_weak', 'nxt', '__weakref__',)
    # mypy doesn't understand that we have a 'prv' attr unless we trick it:
    if _t.TYPE_CHECKING:
        __slots__ = ('prv', 'nxt', '__weakref__')  # pylint: disable=class-variable-slots-conflict

    def __init__(self, prv: '_Node', nxt: '_Node') -> None:
        self.prv = prv
        self.nxt = nxt

    def unlink(self):
        self.prv.nxt = self.nxt
        self.nxt.prv = self.prv


class _SentinelNode(_Node):
    """Special node in a circular doubly-linked list
    that links the first node with the last node.
    When its next and previous references point back to itself
    it represents an empty list.

    To avoid creating a strong reference cycle,
    use weak references to both the next and previous nodes.
    Managing weak references is handled automatically by _WeakAttr.
    """

    nxt: '_Node' = _WeakAttr(slot='_nxt_weak')  # type: ignore[assignment]
    __slots__ = ('_nxt_weak',)

    def __init__(self) -> None:
        super().__init__(self, self)

    def __bool__(self) -> bool:
        return False

    def _iter(self, *, reverse: bool = False) -> _t.Iterator[_Node]:
        """Iterator yielding nodes in the requested order,
        i.e. traverse the linked list via :attr:`nxt`
        (or :attr:`prv` if *reverse* is truthy)
        until reaching a falsy (i.e. sentinel) node.
        """
        attr = 'prv' if reverse else 'nxt'
        node = getattr(self, attr)
        while node:
            yield node
            node = getattr(node, attr)

    def new_last_node(self) -> _Node:
        """Create and return a new terminal node."""
        old_last = self.prv
        new_last = _Node(old_last, self)
        old_last.nxt = self.prv = new_last
        return new_last


class OrderedBidictBase(BidictBase[KT, VT]):
    """Base class implementing an ordered :class:`BidirectionalMapping`."""

    _fwdm_cls: _t.Type[MutableBidirectionalMapping[KT, _Node]] = bidict  # type: ignore [assignment]
    _invm_cls: _t.Type[MutableBidirectionalMapping[VT, _Node]] = bidict  # type: ignore [assignment]
    _fwdm: bidict[KT, _Node]  # type: ignore [assignment]
    _invm: bidict[VT, _Node]  # type: ignore [assignment]

    #: The object used by :meth:`__repr__` for printing the contained items.
    _repr_delegate = list

    @_t.overload
    def __init__(self, __arg: _t.Mapping[KT, VT], **kw: VT) -> None: ...
    @_t.overload
    def __init__(self, __arg: IterItems[KT, VT], **kw: VT) -> None: ...
    @_t.overload
    def __init__(self, **kw: VT) -> None: ...
    def __init__(self, *args: MapOrIterItems[KT, VT], **kw: VT) -> None:
        """Make a new ordered bidirectional mapping.
        The signature behaves like that of :class:`dict`.
        Items passed in are added in the order they are passed,
        respecting the :attr:`on_dup` class attribute in the process.

        The order in which items are inserted is remembered,
        similar to :class:`collections.OrderedDict`.
        """
        self._sntl = _SentinelNode()

        # Like unordered bidicts, ordered bidicts also store two backing one-directional mappings
        # `_fwdm` and `_invm`. But rather than mapping `key` to `val` and `val` to `key`
        # (respectively), they map `key` to `nodefwd` and `val` to `nodeinv` (respectively), where
        # `nodefwd` is `nodeinv` when `key` and `val` are associated with one another.

        # To effect this difference, `_write_item` and `_undo_write` are overridden. But much of the
        # rest of BidictBase's implementation, including BidictBase.__init__ and BidictBase._update,
        # are inherited and are able to be reused without modification.
        super().__init__(*args, **kw)

    if _t.TYPE_CHECKING:
        @property
        def inverse(self) -> 'OrderedBidictBase[VT, KT]': ...

    def _init_inv(self) -> None:
        super()._init_inv()
        self.inverse._sntl = self._sntl

    # Can't reuse BidictBase.copy since ordered bidicts have different internal structure.
    def copy(self: BT) -> BT:
        """A shallow copy of this ordered bidict."""
        # Fast copy implementation bypassing __init__. See comments in :meth:`BidictBase.copy`.
        cp: BT = self.__class__.__new__(self.__class__)
        sntl = _SentinelNode()
        fwdm = copy(self._fwdm)
        invm = copy(self._invm)
        make_node = sntl.new_last_node
        for (key, val) in self.items():
            fwdm[key] = invm[val] = make_node()
        cp._sntl = sntl  # type: ignore [attr-defined]
        cp._fwdm = fwdm
        cp._invm = invm
        cp._init_inv()
        return cp

    __copy__ = copy

    def __getitem__(self, key: KT) -> VT:
        nodefwd = self._fwdm[key]
        val = self._invm.inverse[nodefwd]
        return val

    def _pop(self, key: KT) -> VT:
        nodefwd = self._fwdm.pop(key)
        val = self._invm.inverse.pop(nodefwd)
        nodefwd.unlink()
        return val

    @staticmethod
    def _already_have(key: KT, val: VT, nodeinv: _Node, nodefwd: _Node) -> bool:  # type: ignore [override]
        # Overrides _base.BidictBase.
        return nodeinv is nodefwd

    def _write_item(self, key: KT, val: VT, dedup_result: _DedupResult) -> _WriteResult:
        # Overrides _base.BidictBase.
        fwdm = self._fwdm  # bidict mapping keys to nodes
        invm = self._invm  # bidict mapping vals to nodes
        isdupkey, isdupval, nodeinv, nodefwd = dedup_result
        if not isdupkey and not isdupval:
            # No key or value duplication -> create a new terminal node.
            fwdm[key] = invm[val] = self._sntl.new_last_node()
            oldkey: OKT = _NONE
            oldval: OVT = _NONE
        elif isdupkey and isdupval:
            # Key and value duplication across two different nodes.
            assert nodefwd is not nodeinv
            oldval = invm.inverse[nodefwd]
            oldkey = fwdm.inverse[nodeinv]
            assert oldkey != key
            assert oldval != val
            # We have to collapse nodefwd and nodeinv into a single node, i.e. drop one of them.
            # Drop nodeinv, so that the item with the same key is the one overwritten in place.
            nodeinv.unlink()
            # Don't remove nodeinv's references to its neighbors since
            # if the update fails, we need them to undo this write (see _undo_write below).
            # Update fwdm and invm.
            tmp = fwdm.pop(oldkey)
            assert tmp is nodeinv
            tmp = invm.pop(oldval)
            assert tmp is nodefwd
            fwdm[key] = invm[val] = nodefwd
        elif isdupkey:
            oldval = invm.inverse[nodefwd]
            oldkey = _NONE
            oldnodeinv = invm.pop(oldval)
            assert oldnodeinv is nodefwd
            invm[val] = nodefwd
        else:  # isdupval
            oldkey = fwdm.inverse[nodeinv]
            oldval = _NONE
            oldnodefwd = fwdm.pop(oldkey)
            assert oldnodefwd is nodeinv
            fwdm[key] = nodeinv
        return _WriteResult(key, val, oldkey, oldval)

    def _undo_write(self, dedup_result: _DedupResult, write_result: _WriteResult) -> None:
        fwdm = self._fwdm
        invm = self._invm
        isdupkey, isdupval, nodeinv, nodefwd = dedup_result
        key, val, oldkey, oldval = write_result
        if not isdupkey and not isdupval:
            self._pop(key)
        elif isdupkey and isdupval:
            # Restore original items.
            nodeinv.prv.nxt = nodeinv.nxt.prv = nodeinv
            fwdm[oldkey] = invm[val] = nodeinv
            invm[oldval] = fwdm[key] = nodefwd
        elif isdupkey:
            tmp = invm.pop(val)
            assert tmp is nodefwd
            invm[oldval] = nodefwd
            assert fwdm[key] is nodefwd
        else:  # isdupval
            tmp = fwdm.pop(key)
            assert tmp is nodeinv
            fwdm[oldkey] = nodeinv
            assert invm[val] is nodeinv

    def __iter__(self) -> _t.Iterator[KT]:
        """Iterator over the contained keys in insertion order."""
        return self._iter()

    def _iter(self, *, reverse: bool = False) -> _t.Iterator[KT]:
        key_by_node = self._fwdm._invm
        nodes = self._sntl._iter(reverse=reverse)
        return map(key_by_node.__getitem__, nodes)

    def __reversed__(self) -> _t.Iterator[KT]:
        """Iterator over the contained keys in reverse insertion order."""
        return self._iter(reverse=True)

    def keys(self) -> KeysView[KT]:
        """A set-like object providing a view on the contained keys."""
        return _OrderedBidictKeysView(self)

    # Override the values() inherited from BidictBase merely to override the docstring; the implementation is the same.
    def values(self) -> KeysView[VT]:
        """A set-like object providing a view on the contained items.

        Since the values of a bidict are equivalent to the keys of its inverse,
        this method returns a KeysView for this bidict's inverse
        rather than just a ValuesView for this bidict.
        The KeysView offers the benefit of supporting set operations
        (including constant- rather than linear-time containment checks)
        and is just as cheap to provide as the less capable ValuesView would be.
        """
        return self.inverse.keys()

    def items(self) -> ItemsView[KT, VT]:
        """A set-like object providing a view on the contained items."""
        return _OrderedBidictItemsView(self)


class _OrderedBidictKeysView(KeysView[KT]):
    def __reversed__(self) -> _t.Iterator[KT]:
        return reversed(self._mapping)  # type: ignore[attr-defined]


class _OrderedBidictItemsView(ItemsView[KT, VT]):
    def __reversed__(self) -> _t.Iterator[_t.Tuple[KT, VT]]:
        ob: OrderedBidictBase = self._mapping  # type: ignore[attr-defined]
        key_by_node = ob._fwdm._invm
        val_by_node = ob._invm._invm
        for node in ob._sntl._iter(reverse=True):
            yield (key_by_node[node], val_by_node[node])


#                             * Code review nav *
#==============================================================================
# ← Prev: _bidict.py       Current: _orderedbase.py   Next: _frozenordered.py →
#==============================================================================

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
from weakref import ref as weakref

from ._base import BidictBase
from ._bidict import bidict
from ._typing import KT, VT, OKT, OVT, NONE, IterItems, MapOrIterItems, KeysView, ItemsView


IT = _t.TypeVar('IT')  # instance type
AT = _t.TypeVar('AT')  # attr type


class WeakAttr(_t.Generic[IT, AT]):
    """Automatically handle referencing/dereferencing the given slot as a weakref."""

    def __init__(self, *, slot: str) -> None:
        self.slot = slot

    def __set__(self, instance: IT, value: AT) -> None:
        setattr(instance, self.slot, weakref(value))

    def __get__(self, instance: IT, owner: _t.Any) -> AT:
        return getattr(instance, self.slot)()  # type: ignore [no-any-return]


class Node:
    """A node in a circular doubly-linked list
    used to encode the order of items in an ordered bidict.

    A weak reference to the previous node is stored
    to avoid creating strong reference cycles.
    Referencing/dereferencing the weakref is handled automatically by :class:`WeakAttr`.
    """

    prv: 'WeakAttr[Node, Node]' = WeakAttr(slot='_prv_weak')
    __slots__ = ('_prv_weak', 'nxt', '__weakref__')
    if _t.TYPE_CHECKING:  # no 'prv' in __slots__ makes mypy think we don't have a 'prv' attr, so trick it:
        __slots__ = ('prv', 'nxt', '__weakref__')

    def __init__(self, prv: 'Node', nxt: 'Node') -> None:
        self.prv = prv
        self.nxt = nxt

    def unlink(self) -> None:
        self.prv.nxt = self.nxt
        self.nxt.prv = self.prv


class SentinelNode(Node):
    """Special node in a circular doubly-linked list
    that links the first node with the last node.
    When its next and previous references point back to itself
    it represents an empty list.
    """

    nxt: WeakAttr['SentinelNode', Node] = WeakAttr(slot='_nxt_weak')  # type: ignore [assignment]
    __slots__ = ('_nxt_weak',)

    def __init__(self) -> None:
        super().__init__(self, self)

    def iternodes(self, *, reverse: bool = False) -> _t.Iterator[Node]:
        """Iterator yielding nodes in the requested order,
        i.e. traverse the linked list via :attr:`nxt`
        (or :attr:`prv` if *reverse* is truthy),
        until reaching the sentinel node.
        """
        attr = 'prv' if reverse else 'nxt'
        # Use `while node := getattr(self, attr)` once support for Python 3.7 is dropped.
        node = getattr(self, attr)
        while node is not self:
            yield node
            node = getattr(node, attr)

    def new_last_node(self) -> Node:
        """Create and return a new terminal node."""
        old_last = self.prv
        new_last = Node(old_last, self)
        old_last.nxt = self.prv = new_last
        return new_last


ONODE = _t.Optional[Node]
OrderedWriteResult = _t.Tuple[KT, VT, OKT[KT], OVT[VT], ONODE, ONODE]
OBT = _t.TypeVar('OBT', bound='OrderedBidictBase[_t.Any, _t.Any]')


class OrderedBidictBase(BidictBase[KT, VT]):
    """Base class implementing an ordered :class:`BidirectionalMapping`."""

    #: The object used by :meth:`__repr__` for printing the contained items.
    _repr_delegate = list

    _node_by_key: _t.Optional[bidict[KT, Node]]
    _node_by_val: _t.Optional[bidict[VT, Node]]

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
        self._sntl = SentinelNode()
        self._node_by_key = bidict()
        self._node_by_val = None
        super().__init__(*args, **kw)  # calls _init_inv()

    def _init_inv(self) -> None:
        super()._init_inv()
        self.inverse._sntl = self._sntl
        self.inverse._node_by_key = self._node_by_val
        self.inverse._node_by_val = self._node_by_key

    def _get_node_by_key(self, key: KT) -> _t.Optional[Node]:
        if self._node_by_key is not None:
            return self._node_by_key.get(key)
        if _t.TYPE_CHECKING: assert self._node_by_val is not None
        val: OVT[VT] = self._fwdm.get(key, NONE)
        return self._node_by_val.get(val)  # type: ignore [arg-type]

    def _assoc_node(self, node: Node, key: KT, val: VT) -> None:
        if self._node_by_key is not None:
            self._node_by_key.forceput(key, node)
        else:
            if _t.TYPE_CHECKING: assert self._node_by_val is not None
            self._node_by_val.forceput(val, node)

    def _dissoc_node(self, key: OKT[KT], val: OVT[VT]) -> ONODE:
        if self._node_by_key is not None:
            return self._node_by_key.pop(key, None)  # type: ignore [arg-type]
        if _t.TYPE_CHECKING: assert self._node_by_val is not None
        return self._node_by_val.pop(val, None)  # type: ignore [arg-type]

    if _t.TYPE_CHECKING:
        @property
        def inverse(self) -> 'OrderedBidictBase[VT, KT]': ...

    def _clone_into(self: OBT, other: OBT) -> OBT:
        """See :meth:`bidict.BidictBase.copy`."""
        node_by_korv = self._node_by_key if self._node_by_key is not None else self._node_by_val
        if _t.TYPE_CHECKING: assert node_by_korv is not None
        korv_by_node = node_by_korv.inverse
        o_korv_by_node = korv_by_node.copy()
        other._sntl = SentinelNode()
        new_o_node = other._sntl.new_last_node
        for node in self._sntl.iternodes():
            o_node = new_o_node()
            o_korv_by_node.forceput(o_node, korv_by_node[node])
        other._node_by_key, other._node_by_val = o_korv_by_node.inverse, None
        if self._node_by_key is None:
            other._node_by_key, other._node_by_val = other._node_by_val, other._node_by_key
        return super()._clone_into(other)

    def _pop(self, key: KT) -> VT:
        val = super()._pop(key)
        node = self._dissoc_node(key, val)
        if node is not None:
            node.unlink()
        return val

    def _write(self, newkey: KT, newval: VT, oldkey: OKT[KT], oldval: OVT[VT]) -> OrderedWriteResult[KT, VT]:  # type: ignore [override]
        isdupkey = isdupval = False
        nodek = nodev = dropped_node = None
        if oldval is not NONE:
            isdupkey = True
            nodek = self._get_node_by_key(newkey)
        if oldkey is not NONE:
            isdupval = True
            nodev = self.inverse._get_node_by_key(newval)

        if isdupkey or isdupval:
            self._dissoc_node(oldkey, oldval)

        if not isdupkey and not isdupval:
            # No key or value duplication -> no existing nodes touched.
            assert nodek is None and nodev is None
            # Create a new terminal node.
            assoc_node = self._sntl.new_last_node()
        elif isdupkey and isdupval:
            # Key and value duplication across two different nodes.
            assert nodek is not None and nodev is not None
            # We have to collapse nodek and nodev into a single node, i.e. drop one of them.
            # Drop nodev, so that the item with the same key is the one overwritten in place.
            # But don't remove its references to its neighbors yet, since if the update fails,
            # we use its neighbor references to undo this write (see _undo_write below).
            assoc_node, dropped_node = nodek, nodev
            dropped_node.unlink()
        elif isdupval:
            if _t.TYPE_CHECKING: assert nodev is not None
            assoc_node = nodev
        else:  # isdupkey
            if _t.TYPE_CHECKING: assert nodek is not None
            assoc_node = nodek
        self._assoc_node(assoc_node, newkey, newval)
        base_write = super()._write(newkey, newval, oldkey, oldval)
        return base_write + (assoc_node, dropped_node)

    def _undo_write(self, write_result: OrderedWriteResult[KT, VT]) -> None:  # type: ignore [override]
        *_, oldkey, oldval, assoc_node, dropped_node = write_result
        # mypy does not properly do type narrowing with the following, so inline below instead:
        # isdupkey, isdupval = oldval is not NONE, oldkey is not NONE
        if oldval is not NONE and self._node_by_val is not None:
            assert assoc_node is not None
            self._node_by_val.forceput(oldval, assoc_node)
        if oldkey is not NONE and self._node_by_key is not None:
            assert assoc_node is not None
            self._node_by_key.forceput(oldkey, assoc_node)
        if oldval is not NONE and oldkey is not NONE:
            assert dropped_node is not None
            # Un-collapse nodek and nodev by relinking the node we dropped (nodev). See _write_item above.
            dropped_node.prv.nxt = dropped_node.nxt.prv = dropped_node
        # In the case of not isdupkey and not isdupval, the self._pop() call caused by the following
        # super()._undo_write() call takes care of unmapping and unlinking the new node that was added.
        super()._undo_write(write_result)  # type: ignore [arg-type]

    def __iter__(self) -> _t.Iterator[KT]:
        """Iterator over the contained keys in insertion order."""
        return self._iter(reverse=False)

    def __reversed__(self) -> _t.Iterator[KT]:
        """Iterator over the contained keys in reverse insertion order."""
        return self._iter(reverse=True)

    def _iter(self, *, reverse: bool = False) -> _t.Iterator[KT]:
        nodes = self._sntl.iternodes(reverse=reverse)
        if self._node_by_key is not None:  # Faster than a generator:
            return map(self._node_by_key._invm.__getitem__, nodes)
        assert self._node_by_val is not None
        key_by_val, val_by_node = self._invm, self._node_by_val._invm
        return (key_by_val[val_by_node[node]] for node in nodes)

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
    _mapping: OrderedBidictBase[KT, _t.Any]

    def __reversed__(self) -> _t.Iterator[KT]:
        return reversed(self._mapping)


class _OrderedBidictItemsView(ItemsView[KT, VT]):
    _mapping: OrderedBidictBase[KT, VT]

    def __reversed__(self) -> _t.Iterator[_t.Tuple[KT, VT]]:
        ob = self._mapping
        for key in reversed(ob):
            yield key, ob[key]


def _add_proxy_methods(
    cls: _t.Type[_t.MappingView],
    proxy_to_fwdm_view: str,
    methods: _t.Iterable[str] = (
        '__lt__', '__le__', '__gt__', '__ge__', '__eq__', '__ne__',
        '__or__', '__ror__', '__xor__', '__rxor__', '__and__', '__rand__',
        '__sub__', '__rsub__', 'isdisjoint', '__contains__', '__len__',
    )
) -> None:
    assert proxy_to_fwdm_view in ('keys', 'items')
    def make_proxy_method(methodname: str) -> _t.Any:
        def meth(self: _t.MappingView, *args: _t.Any) -> _t.Any:
            view = getattr(self._mapping._fwdm, proxy_to_fwdm_view)()  # type: ignore [attr-defined]
            meth = getattr(view, methodname)
            return meth(*args)
        meth.__name__ = methodname
        meth.__qualname__ = f'{cls.__qualname__}.{methodname}'
        return meth
    for methodname in methods:
        setattr(cls, methodname, make_proxy_method(methodname))


_add_proxy_methods(_OrderedBidictKeysView, proxy_to_fwdm_view='keys')
_add_proxy_methods(_OrderedBidictItemsView, proxy_to_fwdm_view='items')


#                             * Code review nav *
#==============================================================================
# ← Prev: _bidict.py       Current: _orderedbase.py   Next: _frozenordered.py →
#==============================================================================

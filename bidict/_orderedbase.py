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

import typing as t
from weakref import ref as weakref

from ._base import BidictBase, PreparedWrite
from ._bidict import bidict
from ._typing import KT, VT, OKT, OVT, MISSING, IterItems, MapOrIterItems


IT = t.TypeVar('IT')  # instance type
AT = t.TypeVar('AT')  # attr type


class WeakAttr(t.Generic[IT, AT]):
    """Automatically handle referencing/dereferencing the given slot as a weakref."""

    def __init__(self, *, slot: str) -> None:
        self.slot = slot

    def __set__(self, instance: IT, value: AT) -> None:
        setattr(instance, self.slot, weakref(value))

    def __get__(self, instance: IT, owner: t.Any) -> AT:
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
    if t.TYPE_CHECKING:  # no 'prv' in __slots__ makes mypy think we don't have a 'prv' attr, so trick it:
        __slots__ = ('prv', 'nxt', '__weakref__')

    def __init__(self, prv: 'Node', nxt: 'Node') -> None:
        self.prv = prv
        self.nxt = nxt

    def unlink(self) -> None:
        self.prv.nxt = self.nxt
        self.nxt.prv = self.prv

    def relink(self) -> None:
        self.prv.nxt = self.nxt.prv = self


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

    def iternodes(self, *, reverse: bool = False) -> t.Iterator[Node]:
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


OBT = t.TypeVar('OBT', bound='OrderedBidictBase[t.Any, t.Any]')


NodeByKorV = t.Tuple[bidict, bool]


class OrderedBidictBase(BidictBase[KT, VT]):
    """Base class implementing an ordered :class:`BidirectionalMapping`."""

    #: The object used by :meth:`__repr__` for printing the contained items.
    _repr_delegate = list

    _node_by_korv: NodeByKorV

    @t.overload
    def __init__(self, __arg: t.Mapping[KT, VT], **kw: VT) -> None: ...
    @t.overload
    def __init__(self, __arg: IterItems[KT, VT], **kw: VT) -> None: ...
    @t.overload
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
        self._node_by_korv = bidict(), True
        super().__init__(*args, **kw)  # calls _init_inv()

    def _init_inv(self) -> None:
        super()._init_inv()
        self.inverse._sntl = self._sntl
        node_by_korv, bykey = self._node_by_korv
        self.inverse._node_by_korv = node_by_korv, not bykey

    def _assoc_node(self, node: Node, key: KT, val: VT) -> None:
        node_by_korv, bykey = self._node_by_korv
        korv = key if bykey else val
        node_by_korv.forceput(korv, node)

    def _dissoc_node(self, node: Node) -> None:
        node_by_korv = self._node_by_korv[0]
        del node_by_korv.inverse[node]
        node.unlink()

    if t.TYPE_CHECKING:
        @property
        def inverse(self) -> 'OrderedBidictBase[VT, KT]': ...

    def _init_from(self, other: BidictBase[KT, VT]) -> None:
        """Efficiently clone this ordered bidict by copying its internal structure into *other*."""
        super()._init_from(other)
        node_by_korv, bykey = self._node_by_korv
        korv_by_node = node_by_korv.inverse
        korv_by_node.clear()
        korv_by_node_set = korv_by_node.__setitem__
        self._sntl.nxt = self._sntl.prv = self._sntl
        new_node = self._sntl.new_last_node
        for (k, v) in other.items():
            korv_by_node_set(new_node(), k if bykey else v)

    def _pop(self, key: KT) -> VT:
        val = super()._pop(key)
        node_by_korv, bykey = self._node_by_korv
        node = node_by_korv[key if bykey else val]
        self._dissoc_node(node)
        return val

    def _prep_write(self, newkey: KT, newval: VT, oldkey: OKT[KT], oldval: OVT[VT], save_unwrite: bool) -> PreparedWrite:
        write, unwrite = super()._prep_write(newkey, newval, oldkey, oldval, save_unwrite)
        assoc, dissoc = self._assoc_node, self._dissoc_node
        node_by_korv, bykey = self._node_by_korv
        if oldval is MISSING and oldkey is MISSING:  # no key or value duplication
            # {0: 1, 2: 3} + (4, 5) => {0: 1, 2: 3, 4: 5}
            newnode = self._sntl.new_last_node()
            write.append((assoc, newnode, newkey, newval))
            if save_unwrite:
                unwrite.append((dissoc, newnode))
        elif oldval is not MISSING and oldkey is not MISSING:  # key and value duplication across two different items
            # {0: 1, 2: 3} + (0, 3) => {0: 3}
            #    n1, n2             =>   n1   (collapse n1 and n2 into n1)
            # oldkey: 2, oldval: 1, oldnode: n2, newkey: 0, newval: 3, newnode: n1
            if bykey:
                oldnode = node_by_korv[oldkey]
                newnode = node_by_korv[newkey]
            else:
                oldnode = node_by_korv[newval]
                newnode = node_by_korv[oldval]
            write.extend((
                (dissoc, oldnode),
                (assoc, newnode, newkey, newval),
            ))
            if save_unwrite:
                unwrite.extend((
                    (assoc, newnode, newkey, oldval),
                    (assoc, oldnode, oldkey, newval),
                    (oldnode.relink,),
                ))
        elif oldval is not MISSING:  # just key duplication
            # {0: 1, 2: 3} + (2, 4) => {0: 1, 2: 4}
            # oldkey: MISSING, oldval: 3, newkey: 2, newval: 4
            node = node_by_korv[newkey if bykey else oldval]
            write.append((assoc, node, newkey, newval))
            if save_unwrite:
                unwrite.append((assoc, node, newkey, oldval))
        else:
            assert oldkey is not MISSING  # just value duplication
            # {0: 1, 2: 3} + (4, 3) => {0: 1, 4: 3}
            # oldkey: 2, oldval: MISSING, newkey: 4, newval: 3
            node = node_by_korv[oldkey if bykey else newval]
            write.append((assoc, node, newkey, newval))
            if save_unwrite:
                unwrite.append((assoc, node, oldkey, newval))
        return write, unwrite

    def __iter__(self) -> t.Iterator[KT]:
        """Iterator over the contained keys in insertion order."""
        return self._iter(reverse=False)

    def __reversed__(self) -> t.Iterator[KT]:
        """Iterator over the contained keys in reverse insertion order."""
        return self._iter(reverse=True)

    def _iter(self, *, reverse: bool = False) -> t.Iterator[KT]:
        nodes = self._sntl.iternodes(reverse=reverse)
        node_by_korv, bykey = self._node_by_korv
        # Use map() here because it's faster than using generator comprehensions.
        if bykey:
            return map(node_by_korv._invm.__getitem__, nodes)
        vals = map(node_by_korv._invm.__getitem__, nodes)
        return map(self._invm.__getitem__, vals)

    # Note: We need not override the keys() and items() implementations we inherit
    # from BidictBase, which delegate to the backing _fwdm dict for better performance,
    # since this base class does not implement a mutable bidict, and therefore the
    # ordering of items cannot get out of sync with the backing dict.
    # (In CPython, dicts and dicts' MappingViews are implemented in C, so they are
    # much faster compared to using the implementations we inherit from collections.abc.)
    # In contrast, the subclass OrderedBidict does implement a mutable bidict, and
    # therefore does override these methods, since mutating an existing item after
    # initialization can change the ordering from that of the backing _fwdm dict,
    # and so we have to use the slower __iter__ implementations of the MappingViews
    # in collections.abc to ensure these views continue to yield items in the correct
    # order as an OrderedBidict is mutated.


#                             * Code review nav *
#==============================================================================
# ← Prev: _bidict.py       Current: _orderedbase.py   Next: _frozenordered.py →
#==============================================================================

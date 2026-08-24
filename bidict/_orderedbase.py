# Copyright 2009-2026 Joshua Bronson. All rights reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


#                             * Code review nav *
#                        (see comments in __init__.py)
# ============================================================================
# ← Prev: _bidict.py      Current: _orderedbase.py   Next: _orderedbidict.py →
# ============================================================================


"""Provide :class:`OrderedBidictBase`."""

from __future__ import annotations

import typing as t
from collections.abc import ItemsView
from collections.abc import Iterator
from collections.abc import KeysView
from weakref import ref as weakref

from ._base import BidictBase
from ._base import BidictKeysView
from ._base import ProxiedSetView
from ._base import Unwrites
from ._base import _override_set_methods_to_use_backing_dict
from ._bidict import bidict
from ._iter import iteritems
from ._typing import KT
from ._typing import MISSING
from ._typing import OKT
from ._typing import OVT
from ._typing import VT
from ._typing import MapOrItems
from ._typing import override


AT = t.TypeVar('AT')  # attr type

_MUTATED_DURING_ITERATION: t.Final = 'ordered bidict mutated during iteration'


class WeakAttr(t.Generic[AT]):
    """Descriptor to automatically manage (de)referencing the given slot as a weakref.

    See https://docs.python.org/3/howto/descriptor.html#managed-attributes
    for an intro to using descriptors like this for managed attributes.
    """

    def __init__(self, *, slot: str) -> None:
        self.slot = slot

    def __set__(self, instance: t.Any, value: AT) -> None:
        setattr(instance, self.slot, weakref(value))

    @t.overload
    def __get__(self, instance: None, owner: type) -> t.Self: ...
    @t.overload
    def __get__(self, instance: object, owner: type) -> AT: ...
    def __get__(self, instance: object | None, owner: type) -> t.Self | AT:
        if instance is None:
            return self
        return getattr(instance, self.slot)()  # deref the weakref stored in the slot; typed via the overloads above


class Node:
    """A node in a circular doubly-linked list
    used to encode the order of items in an ordered bidict.

    A weak reference to the previous node is stored
    to avoid creating strong reference cycles.
    Referencing/dereferencing the weakref is handled automatically by :class:`WeakAttr`.
    """

    prv: WeakAttr[Node] = WeakAttr(slot='_prv_weak')
    # nxt is a plain (strong-ref) slot on the base Node; SentinelNode overrides it
    # below with a WeakAttr to break the otherwise-strong cycle around the circular list.
    nxt: Node
    __slots__ = ('__weakref__', '_prv_weak', 'nxt')

    def __init__(self, prv: Node, nxt: Node) -> None:
        self.prv = prv
        self.nxt = nxt

    def unlink(self) -> None:
        """Remove self from in between prv and nxt.
        Self's references to prv and nxt are retained so it can be relinked (see below).
        """
        self.prv.nxt = self.nxt
        self.nxt.prv = self.prv

    def relink(self) -> None:
        """Restore self between prv and nxt after unlinking (see above)."""
        self.prv.nxt = self.nxt.prv = self


class SentinelNode(Node):
    """Special node in a circular doubly-linked list
    that links the first node with the last node.
    When its next and previous references point back to itself
    it represents an empty list.
    """

    nxt: WeakAttr[Node] = WeakAttr(slot='_nxt_weak')  # override base's plain slot with a weakref
    #: Snapshot token, bumped by :meth:`mutated` on every structural change to the list, so
    #: that iterators can detect one. Compared for equality only; its magnitude means nothing.
    #: Lives here rather than on the owning bidict because a bidict and its inverse share this
    #: sentinel, and so must invalidate each other's iterators.
    version: int
    __slots__ = ('_nxt_weak', 'version')

    def __init__(self) -> None:
        self.version = 0
        super().__init__(self, self)

    def mutated(self) -> None:
        """Record a structural change to the list, invalidating any iterators over it."""
        self.version += 1

    def reset(self) -> None:
        """Empty the list."""
        self.nxt = self.prv = self
        self.mutated()

    def iternodes(self, *, reverse: bool = False) -> Iterator[Node]:
        """Iterator yielding nodes in the requested order.

        Raises :class:`RuntimeError` if the list is structurally modified while iterating,
        as :class:`dict` and :class:`collections.OrderedDict` do.
        """
        # Not a generator: the version is captured when the iterator is created rather than when it
        # is first advanced, so mutating in between is detected too, as OrderedDict does.
        return self._iternodes(self.version, reverse=reverse)

    def _iternodes(self, initial_version: int, *, reverse: bool) -> Iterator[Node]:
        # Advance via a literal attr name rather than getattr(node, 'prv' if reverse else 'nxt'):
        # the dynamic lookup the latter needs costs more per node than everything else in
        # this loop put together, since only a literal gets CPython's specialized LOAD_ATTR.
        # (operator.attrgetter does not help: it is a call, not a load.)
        node = self.prv if reverse else self.nxt
        while node is not self:
            if self.version != initial_version:
                raise RuntimeError(_MUTATED_DURING_ITERATION)
            yield node
            node = node.prv if reverse else node.nxt
        # Check on the step that finds the end too, so that a mutation which happens to leave the
        # iterator pointing at the sentinel is caught as well -- e.g. move_to_end() of the item
        # just yielded, which relinks it to exactly where iteration is about to stop.
        if self.version != initial_version:
            raise RuntimeError(_MUTATED_DURING_ITERATION)

    def new_last_node(self) -> Node:
        """Create and return a new terminal node."""
        old_last = self.prv
        new_last = Node(old_last, self)
        old_last.nxt = self.prv = new_last
        self.mutated()
        return new_last


class OrderedBidictBase(BidictBase[KT, VT]):
    """Base class implementing an ordered :class:`BidirectionalMapping`."""

    _node_by_korv: bidict[t.Any, Node]
    _bykey: bool

    def __init__(self, arg: MapOrItems[KT, VT] = (), /, **kw: VT) -> None:
        """Make a new ordered bidirectional mapping.
        The signature behaves like that of :class:`dict`.
        Items passed in are added in the order they are passed,
        respecting the :attr:`~bidict.BidictBase.on_dup`
        class attribute in the process.

        The order in which items are inserted is remembered,
        similar to :class:`collections.OrderedDict`.
        """
        self._sntl = SentinelNode()
        self._node_by_korv = bidict()
        self._bykey = True
        super().__init__(arg, **kw)

    if t.TYPE_CHECKING:

        @property
        @override
        def inverse(self) -> OrderedBidictBase[VT, KT]: ...

        @property
        @override
        def inv(self) -> OrderedBidictBase[VT, KT]: ...

    @override
    def _make_inverse(self) -> OrderedBidictBase[VT, KT]:
        inv = t.cast('OrderedBidictBase[VT, KT]', super()._make_inverse())
        inv._sntl = self._sntl
        inv._node_by_korv = self._node_by_korv
        inv._bykey = not self._bykey
        return inv

    def _assoc_node(self, node: Node, key: KT, val: VT) -> None:
        korv = key if self._bykey else val
        self._node_by_korv.forceput(korv, node)

    def _dissoc_node(self, node: Node) -> None:
        del self._node_by_korv.inverse[node]
        node.unlink()
        self._sntl.mutated()

    def _relink_node(self, node: Node) -> None:
        """Undo a :meth:`_dissoc_node` (the linked list half of it). See :meth:`_write`."""
        node.relink()
        self._sntl.mutated()

    @override
    def _init_from(self, other: MapOrItems[KT, VT]) -> None:
        """See :meth:`BidictBase._init_from`."""
        super()._init_from(other)
        bykey = self._bykey
        korv_by_node = self._node_by_korv.inverse
        korv_by_node.clear()
        korv_by_node_set = korv_by_node.__setitem__
        self._sntl.reset()
        new_node = self._sntl.new_last_node
        for k, v in iteritems(other):
            korv_by_node_set(new_node(), k if bykey else v)

    @override
    def _write(self, newkey: KT, newval: VT, oldkey: OKT[KT], oldval: OVT[VT], unwrites: Unwrites | None) -> None:
        super()._write(newkey, newval, oldkey, oldval, unwrites)
        assoc, dissoc, relink = self._assoc_node, self._dissoc_node, self._relink_node
        node_by_korv, bykey = self._node_by_korv, self._bykey
        if oldval is MISSING and oldkey is MISSING:  # no key or value duplication
            # {0: 1, 2: 3} | {4: 5} => {0: 1, 2: 3, 4: 5}
            newnode = self._sntl.new_last_node()
            assoc(newnode, newkey, newval)
            if unwrites is not None:
                unwrites.append((dissoc, newnode))
        elif oldval is not MISSING and oldkey is not MISSING:  # key and value duplication across two different items
            # {0: 1, 2: 3} | {0: 3} => {0: 3}
            #    n1, n2             =>   n1   (collapse n1 and n2 into n1)
            # oldkey: 2, oldval: 1, oldnode: n2, newkey: 0, newval: 3, newnode: n1
            if bykey:
                oldnode = node_by_korv[oldkey]
                newnode = node_by_korv[newkey]
            else:
                oldnode = node_by_korv[newval]
                newnode = node_by_korv[oldval]
            dissoc(oldnode)
            assoc(newnode, newkey, newval)
            if unwrites is not None:
                unwrites.extend((
                    (assoc, newnode, newkey, oldval),
                    (assoc, oldnode, oldkey, newval),
                    (relink, oldnode),
                ))
        elif oldval is not MISSING:  # just key duplication
            # {0: 1, 2: 3} | {2: 4} => {0: 1, 2: 4}
            # oldkey: MISSING, oldval: 3, newkey: 2, newval: 4
            node = node_by_korv[newkey if bykey else oldval]
            assoc(node, newkey, newval)
            if unwrites is not None:
                unwrites.append((assoc, node, newkey, oldval))
        else:
            assert oldkey is not MISSING  # just value duplication
            # {0: 1, 2: 3} | {4: 3} => {0: 1, 4: 3}
            # oldkey: 2, oldval: MISSING, newkey: 4, newval: 3
            node = node_by_korv[oldkey if bykey else newval]
            assoc(node, newkey, newval)
            if unwrites is not None:
                unwrites.append((assoc, node, oldkey, newval))

    @override
    def __iter__(self) -> Iterator[KT]:
        """Iterator over the contained keys in insertion order."""
        return self._iter(reverse=False)

    @override
    def __reversed__(self) -> Iterator[KT]:
        """Iterator over the contained keys in reverse insertion order."""
        return self._iter(reverse=True)

    def _iter(self, *, reverse: bool = False) -> Iterator[KT]:
        # Not a generator, so that the version is captured now rather than on the first
        # next() call, and an iterator created before a mutation still detects it. Calls
        # _iternodes() directly rather than iternodes(), to skip a call on this hot path.
        sntl = self._sntl
        nodes = sntl._iternodes(sntl.version, reverse=reverse)
        korv_by_node = self._node_by_korv.inverse
        if self._bykey:
            return (korv_by_node[node] for node in nodes)
        key_by_val = self._invm
        return (key_by_val[korv_by_node[node]] for node in nodes)

    # Override the keys() and items() implementations inherited from BidictBase, which may
    # delegate to the backing _fwdm dict: an ordered bidict's order is encoded in its linked
    # list, not in _fwdm, and the two can disagree. That happens after any mutation that
    # changes an existing item, but also during __init__ itself, since a value-duplication
    # overwrite reuses the existing item's node (keeping its position) while _fwdm gets the
    # new key appended and the old one deleted. So these must be overridden here rather than
    # in OrderedBidict, to cover immutable ordered bidicts too.
    @override
    def keys(self) -> KeysView[KT]:
        """A set-like object providing a view on the contained keys."""
        return _OrderedBidictKeysView(self)

    @override
    def items(self) -> ItemsView[KT, VT]:
        """A set-like object providing a view on the contained items."""
        return _OrderedBidictItemsView(self)

    @override
    def values(self) -> BidictKeysView[VT]:
        """A set-like object providing a view on the contained values."""
        # Unlike a non-ordered bidict, whose BidictValuesView has to iterate the backing
        # _fwdm to yield values in key order (see BidictBase.values()), an ordered bidict
        # gets that for free: the inverse shares this bidict's linked list, so its keys
        # view already yields the values in this bidict's order.
        return t.cast('BidictKeysView[VT]', self.inverse.keys())


# The following MappingView implementations use the __iter__ implementations
# inherited from their superclass counterparts in collections.abc, so they
# continue to yield items in the correct order even after an ordered bidict
# is mutated. They also provide a __reversed__ implementation, which is not
# provided by the collections.abc superclasses.
class _OrderedBidictKeysView(ProxiedSetView, BidictKeysView[KT]):
    _mapping: OrderedBidictBase[KT, t.Any]
    _viewname: t.ClassVar[str] = 'keys'
    __slots__ = ()

    def __reversed__(self) -> Iterator[KT]:
        return reversed(self._mapping)


class _OrderedBidictItemsView(ProxiedSetView, ItemsView[KT, VT]):
    _mapping: OrderedBidictBase[KT, VT]
    _viewname: t.ClassVar[str] = 'items'
    __slots__ = ()

    def __reversed__(self) -> Iterator[tuple[KT, VT]]:
        ob = self._mapping
        for key in reversed(ob):
            yield key, ob[key]


_override_set_methods_to_use_backing_dict(_OrderedBidictKeysView)
_override_set_methods_to_use_backing_dict(_OrderedBidictItemsView)


#                             * Code review nav *
# ============================================================================
# ← Prev: _bidict.py      Current: _orderedbase.py   Next: _orderedbidict.py →
# ============================================================================

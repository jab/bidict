# Copyright 2009-2026 Joshua Bronson. All rights reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


#                             * Code review nav *
#                        (see comments in __init__.py)
# ============================================================================
# ← Prev: _orderedbase.py   Current: _orderedbidict.py                   <FIN>
# ============================================================================


"""Provide :class:`OrderedBidict`."""

from __future__ import annotations

import typing as t

from ._bidict import MutableBidict
from ._orderedbase import Node
from ._orderedbase import OrderedBidictBase
from ._typing import KT
from ._typing import VT
from ._typing import override


class OrderedBidict(OrderedBidictBase[KT, VT], MutableBidict[KT, VT]):
    """Mutable bidict type that maintains items in insertion order."""

    if t.TYPE_CHECKING:

        @property
        @override
        def inverse(self) -> OrderedBidict[VT, KT]: ...

        @property
        @override
        def inv(self) -> OrderedBidict[VT, KT]: ...

    @override
    def clear(self) -> None:
        """Remove all items."""
        super().clear()
        self._node_by_korv.clear()
        self._sntl.reset()

    def _node(self, key: KT) -> Node:
        """Return the node of the item with the given key."""
        # Find the node by the contained key (for an inverse, the contained value), not by *key*:
        # _node_by_korv need not resolve an equal but distinct *key* to the same item as a
        # user-supplied _fwdm does (e.g. one that ignores case).
        val = self._fwdm[key]
        return self._node_by_korv[self._invm[val] if self._bykey else val]

    @override
    def _pop(self, key: KT) -> VT:
        # Find the node as _node() does, before removing the item, so that a failed lookup leaves it in place.
        val = self._fwdm[key]
        korv = self._invm[val] if self._bykey else val
        node = self._node_by_korv[korv]
        # Dissociate first, while the item is still contained, since dissociating hashes and may fail.
        # If the removal then fails, restore the node from korv rather than by looking the item up again,
        # which would also hash the other half of the item (whose hash may be what failed).
        self._dissoc_node(node)
        try:
            return super()._pop(key)
        except BaseException:
            self._node_by_korv.forceput(korv, node)
            self._relink_node(node)
            raise

    @override
    def popitem(self, last: bool = True) -> tuple[KT, VT]:
        """*b.popitem() → (k, v)*

        If *last* is true,
        remove and return the most recently added item as a (key, value) pair.
        Otherwise, remove and return the least recently added item.

        :raises KeyError: if *b* is empty.
        """
        if not self:
            raise KeyError('OrderedBidict is empty')
        node = getattr(self._sntl, 'prv' if last else 'nxt')
        korv = self._node_by_korv.inverse[node]
        if self._bykey:
            return korv, self._pop(korv)
        return self.inverse._pop(korv), korv

    def move_to_end(self, key: KT, last: bool = True) -> None:
        """Move the item with the given key to the end if *last* is true, else to the beginning.

        :raises KeyError: if *key* is missing
        """
        node = self._node(key)
        node.prv.nxt = node.nxt
        node.nxt.prv = node.prv
        sntl = self._sntl
        sntl.mutated()
        if last:
            lastnode = sntl.prv
            node.prv = lastnode
            node.nxt = sntl
            sntl.prv = lastnode.nxt = node
        else:
            firstnode = sntl.nxt
            node.prv = sntl
            node.nxt = firstnode
            sntl.nxt = firstnode.prv = node


#                             * Code review nav *
# ============================================================================
# ← Prev: _orderedbase.py   Current: _orderedbidict.py                   <FIN>
# ============================================================================

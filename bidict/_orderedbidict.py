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

    @override
    def _pop(self, key: KT) -> VT:
        val = super()._pop(key)
        node = self._node_by_korv[key if self._bykey else val]
        self._dissoc_node(node)
        return val

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
        korv = key if self._bykey else self._fwdm[key]
        node = self._node_by_korv[korv]
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

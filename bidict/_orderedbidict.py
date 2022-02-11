# Copyright 2009-2022 Joshua Bronson. All Rights Reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


#                             * Code review nav *
#                    (see comments in bidict/__init__.py)
#==============================================================================
#  ← Prev: _frozenordered.py  Current: _orderedbidict.py                <FIN>
#==============================================================================


"""Provide :class:`OrderedBidict`."""

import typing as t

from ._base import BidictKeysView
from ._bidict import MutableBidict
from ._orderedbase import OrderedBidictBase
from ._typing import KT, VT


class OrderedBidict(OrderedBidictBase[KT, VT], MutableBidict[KT, VT]):
    """Mutable bidict type that maintains items in insertion order."""

    if t.TYPE_CHECKING:
        @property
        def inverse(self) -> 'OrderedBidict[VT, KT]': ...

    def clear(self) -> None:
        """Remove all items."""
        super().clear()
        self._node_by_korv.clear()
        self._sntl.nxt = self._sntl.prv = self._sntl

    def _pop(self, key: KT) -> VT:
        val = super()._pop(key)
        node = self._node_by_korv[key if self._bykey else val]
        self._dissoc_node(node)
        return val

    def popitem(self, last: bool = True) -> t.Tuple[KT, VT]:
        """*b.popitem() → (k, v)*

        Remove and return the most recently added item as a (key, value) pair
        if *last* is True, else the least recently added item.

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
        """Move the item with the given key to the end (or beginning if *last* is False).

        :raises KeyError: if *key* is missing
        """
        korv = key if self._bykey else self._fwdm[key]
        node = self._node_by_korv[korv]
        node.prv.nxt = node.nxt
        node.nxt.prv = node.prv
        sntl = self._sntl
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

    # Override the keys() and items() implementations inherited from BidictBase,
    # which may delegate to the backing _fwdm dict, since this is a mutable ordered bidict,
    # and therefore the ordering of items can get out of sync with the backing mappings
    # after mutation. (Need not override values() because it delegates to .inverse.keys().)
    def keys(self) -> t.KeysView[KT]:
        """A set-like object providing a view on the contained keys."""
        return _OrderedBidictKeysView(self)

    def items(self) -> t.ItemsView[KT, VT]:
        """A set-like object providing a view on the contained items."""
        return _OrderedBidictItemsView(self)


# The following MappingView implementations use the __iter__ implementations
# inherited from their superclass counterparts in collections.abc, so they
# continue to yield items in the correct order even after an OrderedBidict
# is mutated. They also provide a __reversed__ implementation, which is not
# provided by the collections.abc superclasses.
class _OrderedBidictKeysView(BidictKeysView[KT]):
    _mapping: OrderedBidict[KT, t.Any]

    def __reversed__(self) -> t.Iterator[KT]:
        return reversed(self._mapping)


class _OrderedBidictItemsView(t.ItemsView[KT, VT]):
    _mapping: OrderedBidict[KT, VT]

    def __reversed__(self) -> t.Iterator[t.Tuple[KT, VT]]:
        ob = self._mapping
        for key in reversed(ob):
            yield key, ob[key]


# Although the OrderedBidict MappingViews above cannot delegate to a backing dict's
# MappingViews for faster __iter__ and __reversed__ implementations, they can for all
# the collections.abc.Set methods (since they're not order-sensitive), so we make that
# happen below. https://bugs.python.org/issue46713 tracks providing C implementations
# of the collections.abc MappingViews, which would make the below unnecessary.

OBKeysOrItemsView = t.Union[_OrderedBidictKeysView[KT], _OrderedBidictItemsView[KT, VT]]
OBKeysOrItemsViewT = t.Union[t.Type[_OrderedBidictKeysView[KT]], t.Type[_OrderedBidictItemsView[KT, VT]]]


def _add_proxy_methods(
    cls: OBKeysOrItemsViewT[KT, VT],
    viewname: str,  # Use t.Literal['keys', 'items'] when support for Python 3.7 is dropped.
    methods: t.Iterable[str] = (
        '__lt__', '__le__', '__gt__', '__ge__', '__eq__', '__ne__',
        '__or__', '__ror__', '__xor__', '__rxor__', '__and__', '__rand__',
        '__sub__', '__rsub__', 'isdisjoint', '__contains__', '__len__',
    )
) -> None:
    assert viewname in ('keys', 'items')

    def make_proxy_method(methodname: str) -> t.Any:
        def meth(self: OBKeysOrItemsView[KT, VT], *args: t.Any) -> t.Any:
            self_bi = self._mapping
            fwdm_view = getattr(self_bi._fwdm, viewname)()
            if len(args) == 1 and isinstance(args[0], (_OrderedBidictKeysView, _OrderedBidictItemsView)):
                other_bi = args[0]._mapping
                other_view = getattr(other_bi._fwdm, viewname)()
                args = (other_view,)
            return getattr(fwdm_view, methodname)(*args)
        meth.__name__ = methodname
        meth.__qualname__ = f'{cls.__qualname__}.{methodname}'
        return meth

    for methodname in methods:
        setattr(cls, methodname, make_proxy_method(methodname))


_add_proxy_methods(_OrderedBidictKeysView, 'keys')
_add_proxy_methods(_OrderedBidictItemsView, 'items')


#                             * Code review nav *
#==============================================================================
#  ← Prev: _frozenordered.py  Current: _orderedbidict.py                <FIN>
#==============================================================================

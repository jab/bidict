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
from collections.abc import ItemsView
from collections.abc import Iterable
from collections.abc import Iterator
from collections.abc import KeysView
from collections.abc import Set

from ._base import BidictKeysView
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
        self._sntl.nxt = self._sntl.prv = self._sntl

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
    @override
    def keys(self) -> KeysView[KT]:
        """A set-like object providing a view on the contained keys."""
        return _OrderedBidictKeysView(self)

    @override
    def items(self) -> ItemsView[KT, VT]:
        """A set-like object providing a view on the contained items."""
        return _OrderedBidictItemsView(self)


# The following MappingView implementations use the __iter__ implementations
# inherited from their superclass counterparts in collections.abc, so they
# continue to yield items in the correct order even after an OrderedBidict
# is mutated. They also provide a __reversed__ implementation, which is not
# provided by the collections.abc superclasses.
class _OrderedBidictKeysView(BidictKeysView[KT]):
    _mapping: OrderedBidict[KT, t.Any]
    _viewname: t.ClassVar[str] = 'keys'

    def __reversed__(self) -> Iterator[KT]:
        return reversed(self._mapping)


class _OrderedBidictItemsView(ItemsView[KT, VT]):
    _mapping: OrderedBidict[KT, VT]
    _viewname: t.ClassVar[str] = 'items'

    def __reversed__(self) -> Iterator[tuple[KT, VT]]:
        ob = self._mapping
        for key in reversed(ob):
            yield key, ob[key]


# For better performance, make _OrderedBidictKeysView and _OrderedBidictItemsView delegate
# to backing dicts for the methods they inherit from collections.abc.Set. (Cannot delegate
# for __iter__ and __reversed__ since they are order-sensitive.) See also: https://bugs.python.org/issue46713
_OView: t.TypeAlias = type[_OrderedBidictKeysView[KT]] | type[_OrderedBidictItemsView[KT, t.Any]]
_setmethodnames: Iterable[str] = (
    '__lt__',
    '__le__',
    '__gt__',
    '__ge__',
    '__eq__',
    '__ne__',
    '__sub__',
    '__rsub__',
    '__or__',
    '__ror__',
    '__xor__',
    '__rxor__',
    '__and__',
    '__rand__',
    'isdisjoint',
)


def _override_set_methods_to_use_backing_dict(cls: _OView[KT]) -> None:
    def make_proxy_method(methodname: str) -> t.Any:
        def method(self: _OrderedBidictKeysView[KT] | _OrderedBidictItemsView[KT, t.Any], *args: t.Any) -> t.Any:
            fwdm = self._mapping._fwdm
            if not isinstance(fwdm, dict):  # dict view speedup not available, fall back to Set's implementation.
                return getattr(Set, methodname)(self, *args)
            fwdm_dict_view = getattr(fwdm, self._viewname)()
            fwdm_dict_view_method = getattr(fwdm_dict_view, methodname)
            # When the (single) arg is another _OrderedBidict{Keys,Items}View backed by a dict, forward its
            # backing dict_keys/dict_items to the C-level method rather than the arg itself. C-level dict views
            # only interoperate with other C-level dict views, not with arbitrary Set subclasses, so e.g.
            # `dict_keys(ob1).__lt__(ob2.keys())` returns NotImplemented. With both sides returning
            # NotImplemented, Python either raises TypeError (for `<`, `<=`, `>`, `>=`) or falls back to the
            # wrong answer (e.g. identity-based `==`). Note arg's view may differ from self's (keys vs items),
            # so use arg._viewname; this also subsumes the same-type case, where it equals self._viewname.
            if (
                len(args) == 1
                and isinstance((arg := args[0]), (_OrderedBidictKeysView, _OrderedBidictItemsView))
                and isinstance(arg._mapping._fwdm, dict)
            ):
                arg_dict_view = getattr(arg._mapping._fwdm, arg._viewname)()
                return fwdm_dict_view_method(arg_dict_view)
            return fwdm_dict_view_method(*args)

        method.__name__ = methodname
        method.__qualname__ = f'{cls.__qualname__}.{methodname}'
        return method

    for name in _setmethodnames:
        setattr(cls, name, make_proxy_method(name))


_override_set_methods_to_use_backing_dict(_OrderedBidictKeysView)
_override_set_methods_to_use_backing_dict(_OrderedBidictItemsView)


#                             * Code review nav *
# ============================================================================
# ← Prev: _orderedbase.py   Current: _orderedbidict.py                   <FIN>
# ============================================================================

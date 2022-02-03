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
#  ← Prev: _frozenordered.py  Current: _orderedbidict.py                <FIN>
#==============================================================================


"""Provide :class:`OrderedBidict`."""

import typing as t

from ._base import BiMappingView, BiKeysView, BiItemsView
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
        self._node_by_korv[0].clear()
        self._sntl.nxt = self._sntl.prv = self._sntl

    def popitem(self, last: bool = True) -> t.Tuple[KT, VT]:
        """*b.popitem() → (k, v)*

        Remove and return the most recently added item as a (key, value) pair
        if *last* is True, else the least recently added item.

        :raises KeyError: if *b* is empty.
        """
        if not self:
            raise KeyError('mapping is empty')  # match {}.pop() and bidict().pop()
        node = getattr(self._sntl, 'prv' if last else 'nxt')
        node_by_korv, bykey = self._node_by_korv
        korv = node_by_korv.inverse[node]
        if bykey:
            return korv, self._pop(korv)
        return self.inverse._pop(korv), korv

    def move_to_end(self, key: KT, last: bool = True) -> None:
        """Move an existing key to the beginning or end of this ordered bidict.

        The item is moved to the end if *last* is True, else to the beginning.

        :raises KeyError: if the key does not exist
        """
        node_by_korv, bykey = self._node_by_korv
        korv = key if bykey else self._fwdm[key]
        node = node_by_korv[korv]
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

    # Override the keys() and items() implementations we inherit from BidictBase,
    # which delegate to the backing _fwdm dict for better performance,
    # since this is a mutable ordered bidict, and therefore the ordering of items
    # can get out of sync with the backing dict after mutation.
    # (We need not override values() because it just delegates to .inverse.keys().)
    def keys(self) -> BiKeysView[KT, VT]:
        """A set-like object providing a view on the contained keys."""
        return _OrderedBidictKeysView(self)

    def items(self) -> BiItemsView[KT, VT]:
        """A set-like object providing a view on the contained items."""
        return _OrderedBidictItemsView(self)


# The following MappingView implementations use the __iter__ implementations
# inherited from their superclass counterparts in collections.abc, so they
# continue to yield items in the correct order even after an OrderedBidict
# is mutated. They also provide a __reversed__ implementation, which is not
# provided by the collections.abc superclasses.
class _OrderedBidictKeysView(BiKeysView[KT, VT]):
    _mapping: OrderedBidict[KT, VT]

    def __reversed__(self) -> t.Iterator[KT]:
        return reversed(self._mapping)


class _OrderedBidictItemsView(BiItemsView[KT, VT]):
    _mapping: OrderedBidict[KT, VT]

    def __reversed__(self) -> t.Iterator[t.Tuple[KT, VT]]:
        ob = self._mapping
        for key in reversed(ob):
            yield key, ob[key]


# Although the OrderedBidict MappingViews above cannot delegate to a backing
# dict's MappingViews for faster __iter__ and __reversed__ implementations,
# they can for all the collections.abc.Set methods, which are not order-sensitive:
def _add_proxy_methods(
    cls: t.Type[BiMappingView[KT, VT]],
    viewname: str,
    methods: t.Iterable[str] = (
        '__lt__', '__le__', '__gt__', '__ge__', '__eq__', '__ne__',
        '__or__', '__ror__', '__xor__', '__rxor__', '__and__', '__rand__',
        '__sub__', '__rsub__', 'isdisjoint', '__contains__', '__len__',
    )
) -> None:
    assert viewname in ('keys', 'items')

    def make_proxy_method(methodname: str) -> t.Any:
        def meth(self: BiMappingView[KT, VT], *args: t.Any) -> t.Any:
            self_bi = self._mapping
            fwdm_view = getattr(self_bi._fwdm, viewname)()
            if len(args) == 1 and isinstance(args[0], BiMappingView):
                other_bi = args[0]._mapping
                other_view = getattr(other_bi._fwdm, viewname)()
                args = (other_view,)
            rv = getattr(fwdm_view, methodname)(*args)
            if rv is NotImplemented:
                print(f'{fwdm_view}.{methodname}(*{args}) is NotImplemented')
            return rv
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

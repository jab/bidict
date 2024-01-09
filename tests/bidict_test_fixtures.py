# Copyright 2009-2024 Joshua Bronson. All rights reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import annotations

import operator
import typing as t
from collections import UserDict
from dataclasses import dataclass
from itertools import starmap

from bidict import DROP_NEW
from bidict import DROP_OLD
from bidict import RAISE
from bidict import BidictBase
from bidict import DuplicationError
from bidict import KeyAndValueDuplicationError
from bidict import KeyDuplicationError
from bidict import MutableBidirectionalMapping
from bidict import OnDup
from bidict import OrderedBidict
from bidict import ValueDuplicationError
from bidict import bidict
from bidict import frozenbidict
from bidict._typing import MapOrItems


KT = t.TypeVar('KT')
VT = t.TypeVar('VT')


class SupportsKeysAndGetItem(t.Generic[KT, VT]):
    def __init__(self, *args: t.Any, **kw: t.Any) -> None:
        self._mapping: t.Mapping[KT, VT] = dict(*args, **kw)

    def keys(self) -> t.KeysView[KT]:
        return self._mapping.keys()

    def __getitem__(self, key: KT) -> VT:
        return self._mapping[key]


BB: t.TypeAlias = BidictBase[KT, VT]
BT: t.TypeAlias = t.Type[BB[KT, VT]]
user_bidict_types: list[BT[t.Any, t.Any]] = []


def user_bidict(cls: BT[KT, VT]) -> BT[KT, VT]:
    user_bidict_types.append(cls)
    return cls


@user_bidict
class UserBi(bidict[KT, VT]):
    _fwdm_cls = UserDict
    _invm_cls = UserDict


@user_bidict
class UserOrderedBi(OrderedBidict[KT, VT]):
    _fwdm_cls = UserDict
    _invm_cls = UserDict


@user_bidict
class UserBiNotOwnInv(bidict[KT, VT]):
    """A custom bidict whose inverse class is not itself."""

    _fwdm_cls = dict
    _invm_cls = UserDict


UserBiNotOwnInvInv = UserBiNotOwnInv._inv_cls
assert UserBiNotOwnInvInv is not UserBiNotOwnInv

BTs: t.TypeAlias = t.Tuple[BT[t.Any, t.Any], ...]
builtin_bidict_types: BTs = (bidict, frozenbidict, OrderedBidict)
bidict_types: BTs = (*builtin_bidict_types, *user_bidict_types)
update_arg_types = (*bidict_types, list, dict, iter, SupportsKeysAndGetItem)
mutable_bidict_types: BTs = tuple(t for t in bidict_types if issubclass(t, MutableBidirectionalMapping))
assert frozenbidict not in mutable_bidict_types
MBT: t.TypeAlias = t.Union[t.Type[bidict[KT, VT]], t.Type[OrderedBidict[KT, VT]]]


def should_be_reversible(bi_t: BT[KT, VT]) -> bool:
    return bi_t in builtin_bidict_types or issubclass(bi_t, OrderedBidict)


assert all(not should_be_reversible(bi_t) or issubclass(bi_t, t.Reversible) for bi_t in bidict_types)


SET_OPS: t.Any = (
    operator.le,
    operator.lt,
    operator.gt,
    operator.ge,
    operator.eq,
    operator.ne,
    operator.and_,
    operator.or_,
    operator.sub,
    operator.xor,
    (lambda x, y: x.isdisjoint(y)),
)


DEFAULT_ON_DUP = OnDup(DROP_OLD, RAISE)


@dataclass
class Oracle(t.Generic[KT, VT]):
    data: dict[KT, VT]
    ordered: bool

    @property
    def data_inv(self) -> dict[VT, KT]:
        return {v: k for (k, v) in self.data.items()}

    def assert_match(self, bi: BidictBase[KT, VT]) -> None:
        assert dict(bi) == self.data
        assert dict(bi.inv) == self.data_inv
        self.assert_items_match(bi)

    def assert_items_match(self, bi: BidictBase[KT, VT]) -> None:
        if self.ordered:
            assert zip_equal(bi.items(), self.data.items())
        else:
            assert bi.items() == self.data.items()

    def clear(self) -> None:
        self.data.clear()

    def pop(self, key: KT) -> VT:
        return self.data.pop(key)

    def popitem(self, last: bool = True) -> tuple[KT, VT]:
        if last:
            return self.data.popitem()
        key = next(iter(self.data))
        return key, self.data.pop(key)

    def put(self, key: KT, val: VT, on_dup: OnDup = DEFAULT_ON_DUP) -> None:
        oldval = self.data.get(key)
        oldkey = self.data_inv.get(val)
        isdupkey = oldval is not None
        isdupval = oldkey is not None
        if isdupkey and isdupval:
            if key == oldkey:  # (key, val) duplicates an existing item -> no-op
                assert val == oldval
                return
            # key and val each duplicate a different existing item.
            if on_dup.val is RAISE:
                raise KeyAndValueDuplicationError(key, val)
            if on_dup.val is DROP_NEW:
                return
            assert on_dup.val is DROP_OLD
        elif isdupkey:
            if on_dup.key is RAISE:
                raise KeyDuplicationError(key)
            if on_dup.key is DROP_NEW:
                return
            assert on_dup.key is DROP_OLD
        elif isdupval:
            if on_dup.val is RAISE:
                raise ValueDuplicationError(val)
            if on_dup.val is DROP_NEW:
                return
            assert on_dup.val is DROP_OLD
        if not self.ordered:
            self.data[key] = val
            self.data.pop(oldkey, None)  # type: ignore[arg-type]
            return
        # Ensure insertion order is preserved in the case of a sequence of overwriting updates.
        updated = {}
        for k, v in self.data.items():
            if k == oldkey or v == oldval:
                if k == oldkey and isdupkey and isdupval:
                    continue
                updated[key] = val
            else:
                updated[k] = v
        updated[key] = val
        self.data = updated

    def putall(self, updates: MapOrItems[KT, VT], on_dup: OnDup = DEFAULT_ON_DUP) -> None:
        # https://bidict.readthedocs.io/en/main/basic-usage.html#order-matters
        tmp = self.data.copy()
        if isinstance(updates, t.Mapping):
            updates = updates.items()
        elif hasattr(updates, 'keys') and hasattr(updates, '__getitem__'):
            updates = [(k, updates[k]) for k in updates.keys()]
        try:
            for key, val in updates:
                self.put(key, val, on_dup)
        except DuplicationError:
            self.data = tmp  # fail clean (no partially-applied updates)
            raise

    def __ior__(self, other: t.Mapping[KT, VT]) -> dict[KT, VT]:
        self.putall(other)
        return self.data

    def __or__(self, other: t.Mapping[KT, VT]) -> dict[KT, VT]:
        before = self.data.copy()
        self.putall(other)
        after = self.data
        self.data = before
        return after

    def __ror__(self, other: t.Mapping[KT, VT]) -> dict[KT, VT]:
        before = self.data.copy()
        self.data = {}
        try:
            self.putall(other)
            self.putall(before)
        except DuplicationError:
            self.data = before
            raise
        after = self.data
        self.data = before
        return after

    def move_to_end(self, key: KT, last: bool = True) -> None:
        val = self.pop(key)
        if last:
            self.put(key, val)
        else:
            self.data = {key: val, **self.data}


def zip_equal(i1: t.Iterable[t.Any], i2: t.Iterable[t.Any]) -> bool:
    return all(starmap(operator.eq, zip(i1, i2)))


def invdict(d: dict[KT, VT]) -> dict[VT, KT]:
    return {v: k for (k, v) in d.items()}


def dedup(x: MapOrItems[KT, VT]) -> dict[KT, VT]:
    return invdict(invdict(dict(x)))

# Copyright 2009-2023 Joshua Bronson. All rights reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Types for Hypothoses tests."""

from __future__ import annotations

import typing as t
from collections import OrderedDict
from collections import UserDict

from bidict import BidictBase
from bidict import FrozenOrderedBidict
from bidict import OrderedBidict
from bidict import bidict
from bidict import frozenbidict


KT = t.TypeVar('KT')
VT = t.TypeVar('VT')
BiTypesT: t.TypeAlias = t.Tuple[t.Type[BidictBase[t.Any, t.Any]], ...]


class UserBidict(bidict[KT, VT]):
    """Custom bidict subclass."""

    _fwdm_cls = UserDict
    _invm_cls = UserDict


class UserOrderedBidict(OrderedBidict[KT, VT]):
    """Custom OrderedBidict subclass."""

    _fwdm_cls = UserDict
    _invm_cls = UserDict


class UserBidictNotOwnInverse(bidict[KT, VT]):
    """Custom bidict subclass that is not its own inverse."""

    _fwdm_cls = dict
    _invm_cls = UserDict


UserBidictNotOwnInverseInv = UserBidictNotOwnInverse._inv_cls
assert UserBidictNotOwnInverseInv is not UserBidictNotOwnInverse


class UserBidictNotOwnInverse2(UserBidictNotOwnInverse[KT, VT]):
    """Another custom bidict subclass that is not its own inverse."""


MUTABLE_BIDICT_TYPES: BiTypesT = (
    bidict,
    OrderedBidict,
    UserBidict,
    UserOrderedBidict,
    UserBidictNotOwnInverse,
)
FROZEN_BIDICT_TYPES: BiTypesT = (frozenbidict, FrozenOrderedBidict)
ORDERED_BIDICT_TYPES: BiTypesT = (OrderedBidict, FrozenOrderedBidict, UserOrderedBidict)
ORDER_PRESERVING_BIDICT_TYPES: BiTypesT = tuple(set(FROZEN_BIDICT_TYPES + ORDERED_BIDICT_TYPES))
BIDICT_TYPES: BiTypesT = tuple(set(MUTABLE_BIDICT_TYPES + FROZEN_BIDICT_TYPES + ORDERED_BIDICT_TYPES))
# When support is dropped for Python < 3.8, all bidict types will be reversible,
# and we can remove the following and just use BIDICT_TYPES instead:
REVERSIBLE_BIDICT_TYPES: BiTypesT = tuple(b for b in BIDICT_TYPES if issubclass(b, t.Reversible))

BIDICT_TYPE_WHOSE_MODULE_HAS_REF_TO_INV_CLS = UserBidictNotOwnInverse
BIDICT_TYPE_WHOSE_MODULE_HAS_NO_REF_TO_INV_CLS = UserBidictNotOwnInverse2


class SupportsKeysAndGetItem(t.Generic[KT, VT]):
    def __init__(self, *args: t.Any, **kw: t.Any) -> None:
        self._mapping: t.Mapping[KT, VT] = dict(*args, **kw)

    def keys(self) -> t.KeysView[KT]:
        return self._mapping.keys()

    def __getitem__(self, key: KT) -> VT:
        return self._mapping[key]


class _FrozenMap(t.Mapping[KT, VT]):
    def __init__(self, *args: t.Any, **kw: t.Any) -> None:
        self._mapping: t.Mapping[KT, VT] = dict(*args, **kw)

    def __iter__(self) -> t.Iterator[KT]:
        return iter(self._mapping)

    def __len__(self) -> int:
        return len(self._mapping)

    def __getitem__(self, key: KT) -> VT:
        return self._mapping[key]

    def __hash__(self) -> int:
        return t.ItemsView(self._mapping)._hash()


NON_BI_MAPPING_TYPES = (dict, OrderedDict, _FrozenMap)
MAPPING_TYPES = BIDICT_TYPES + NON_BI_MAPPING_TYPES
ORDERED_MAPPING_TYPES = (*ORDERED_BIDICT_TYPES, OrderedDict)
HASHABLE_MAPPING_TYPES = (*FROZEN_BIDICT_TYPES, _FrozenMap)

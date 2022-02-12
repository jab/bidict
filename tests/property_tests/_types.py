# Copyright 2009-2022 Joshua Bronson. All Rights Reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Types for Hypothoses tests."""

from collections import OrderedDict, UserDict
from collections.abc import ItemsView, Mapping, Reversible

from bidict import FrozenOrderedBidict, OrderedBidict, bidict, frozenbidict, namedbidict


class UserBidict(bidict):
    """Custom bidict subclass."""

    _fwdm_cls = UserDict
    _invm_cls = UserDict


class UserOrderedBidict(OrderedBidict):
    """Custom OrderedBidict subclass."""

    _fwdm_cls = UserDict
    _invm_cls = UserDict


class UserBidictNotOwnInverse(bidict):
    """Custom bidict subclass that is not its own inverse."""

    _fwdm_cls = dict
    _invm_cls = UserDict


UserBidictNotOwnInverseInv = UserBidictNotOwnInverse._inv_cls
assert UserBidictNotOwnInverseInv is not UserBidictNotOwnInverse


class UserBidictNotOwnInverse2(UserBidictNotOwnInverse):
    """Another custom bidict subclass that is not its own inverse."""


NamedBidict = namedbidict('NamedBidict', 'key', 'val', base_type=bidict)
NamedFrozenBidict = namedbidict('NamedFrozenBidict', 'key', 'val', base_type=frozenbidict)
NamedOrderedBidict = namedbidict('NamedOrderedBidict', 'key', 'val', base_type=OrderedBidict)
NamedUserBidict = namedbidict('NamedUserBidict', 'key', 'val', base_type=UserBidict)
NAMED_BIDICT_TYPES = (NamedBidict, NamedFrozenBidict, NamedOrderedBidict, NamedUserBidict)

MUTABLE_BIDICT_TYPES = (bidict, OrderedBidict, NamedBidict, UserBidict, UserOrderedBidict, UserBidictNotOwnInverse)
FROZEN_BIDICT_TYPES = (frozenbidict, FrozenOrderedBidict, NamedFrozenBidict)
ORDERED_BIDICT_TYPES = (OrderedBidict, FrozenOrderedBidict, NamedOrderedBidict, UserOrderedBidict)
ORDER_PRESERVING_BIDICT_TYPES = tuple(set(FROZEN_BIDICT_TYPES + ORDERED_BIDICT_TYPES))
BIDICT_TYPES = tuple(set(MUTABLE_BIDICT_TYPES + FROZEN_BIDICT_TYPES + ORDERED_BIDICT_TYPES))
NON_NAMED_BIDICT_TYPES = tuple(set(BIDICT_TYPES) - set(NAMED_BIDICT_TYPES))
# When support is dropped for Python < 3.8, all bidict types will be reversible,
# and we can remove the following and just use BIDICT_TYPES instead:
REVERSIBLE_BIDICT_TYPES = tuple(b for b in BIDICT_TYPES if issubclass(b, Reversible))

BIDICT_TYPE_WHOSE_MODULE_HAS_REF_TO_INV_CLS = UserBidictNotOwnInverse
BIDICT_TYPE_WHOSE_MODULE_HAS_NO_REF_TO_INV_CLS = UserBidictNotOwnInverse2


class _FrozenMap(Mapping):

    def __init__(self, *args, **kw):
        self._mapping = dict(*args, **kw)

    def __iter__(self):
        return iter(self._mapping)

    def __len__(self):
        return len(self._mapping)

    def __getitem__(self, key):
        return self._mapping[key]

    def __hash__(self):
        return ItemsView(self._mapping)._hash()


NON_BI_MAPPING_TYPES = (dict, OrderedDict, _FrozenMap)
MAPPING_TYPES = BIDICT_TYPES + NON_BI_MAPPING_TYPES
ORDERED_MAPPING_TYPES = ORDERED_BIDICT_TYPES + (OrderedDict,)
HASHABLE_MAPPING_TYPES = FROZEN_BIDICT_TYPES + (_FrozenMap,)

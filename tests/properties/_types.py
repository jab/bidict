# -*- coding: utf-8 -*-
# Copyright 2009-2020 Joshua Bronson. All Rights Reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Types for Hypothoses tests."""

from collections import OrderedDict
from collections.abc import KeysView, ItemsView, Mapping

from bidict import FrozenOrderedBidict, OrderedBidict, bidict, frozenbidict, namedbidict


MyNamedBidict = namedbidict('MyNamedBidict', 'key', 'val', base_type=bidict)
MyNamedFrozenBidict = namedbidict('MyNamedFrozenBidict', 'key', 'val', base_type=frozenbidict)
MyNamedOrderedBidict = namedbidict('MyNamedOrderedBidict', 'key', 'val', base_type=OrderedBidict)
MUTABLE_BIDICT_TYPES = (bidict, OrderedBidict, MyNamedBidict)
FROZEN_BIDICT_TYPES = (frozenbidict, FrozenOrderedBidict, MyNamedFrozenBidict)
ORDERED_BIDICT_TYPES = (OrderedBidict, FrozenOrderedBidict, MyNamedOrderedBidict)
BIDICT_TYPES = tuple(set(MUTABLE_BIDICT_TYPES + FROZEN_BIDICT_TYPES + ORDERED_BIDICT_TYPES))


class _FrozenDict(KeysView, Mapping):

    def __init__(self, *args, **kw):
        self._mapping = dict(*args, **kw)

    def __getitem__(self, key):
        return self._mapping[key]

    def __hash__(self):
        return ItemsView(self._mapping)._hash()


NON_BIDICT_MAPPING_TYPES = (dict, OrderedDict, _FrozenDict)
MAPPING_TYPES = BIDICT_TYPES + NON_BIDICT_MAPPING_TYPES
ORDERED_MAPPING_TYPES = ORDERED_BIDICT_TYPES + (OrderedDict,)
HASHABLE_MAPPING_TYPES = FROZEN_BIDICT_TYPES + (_FrozenDict,)

# -*- coding: utf-8 -*-
# Copyright 2018 Joshua Bronson. All Rights Reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Equality and hashing tests."""

from collections import Counter, Hashable, OrderedDict, Mapping, defaultdict
from itertools import product

import pytest
from bidict import FrozenOrderedBidict, OrderedBidict, bidict, namedbidict, frozenbidict


class _DictSubcls(dict):
    pass


class _OrderedBidictSubcls(OrderedBidict):
    pass


ITEMS = [('a', 1), ('b', 2)]  # use int values so we can use with Counter below
ITEMS_REV = list(reversed(ITEMS))

BIDICT = bidict(ITEMS)
FROZEN = frozenbidict(ITEMS)
NAMED = namedbidict('named', 'keys', 'vals')(ITEMS)
ORDERED = OrderedBidict(ITEMS)
ORDERED_REV = OrderedBidict(ITEMS_REV)
ORDERED_SUB = _OrderedBidictSubcls(ITEMS)
ORDERED_SUB_REV = _OrderedBidictSubcls(ITEMS_REV)
FROZEN_ORDERED = FrozenOrderedBidict(ITEMS)
FROZEN_ORDERED_REV = FrozenOrderedBidict(ITEMS_REV)
BIDICTS = (
    BIDICT,
    FROZEN,
    NAMED,
    ORDERED,
    ORDERED_REV,
    ORDERED_SUB,
    ORDERED_SUB_REV,
    FROZEN_ORDERED,
    FROZEN_ORDERED_REV,
)

DICT_REV = dict(ITEMS_REV)
COUNTER_REV = Counter(DICT_REV)
DEFAULTDICT_REV = defaultdict(lambda x: None, ITEMS_REV)
DICT_SUB_REV = _DictSubcls(ITEMS_REV)
ORDERED_DICT = OrderedDict(ITEMS)
ORDERED_DICT_REV = OrderedDict(ITEMS_REV)
EMPTY_DICT = {}
NOT_A_MAPPING = 42
NOT_BIDICTS = (
    DICT_REV,
    COUNTER_REV,
    DEFAULTDICT_REV,
    DICT_SUB_REV,
    ORDERED_DICT,
    ORDERED_DICT_REV,
    EMPTY_DICT,
    NOT_A_MAPPING,
)


@pytest.mark.parametrize('some_bidict, other', product(BIDICTS, BIDICTS + NOT_BIDICTS))
def test_eq_and_hash(some_bidict, other):
    """Make sure equality tests and hash results behave as expected."""
    b_has_eq_order_sens = hasattr(some_bidict, 'equals_order_sensitive')
    if not isinstance(other, Mapping):
        assert some_bidict != other
        if b_has_eq_order_sens:
            assert not some_bidict.equals_order_sensitive(other)
    elif len(some_bidict) != len(other):
        assert some_bidict != other
    else:
        should_be_equal = dict(some_bidict) == dict(other)
        are_equal = some_bidict == other
        assert are_equal == should_be_equal
        both_hashable = isinstance(some_bidict, Hashable) and isinstance(other, Hashable)
        if are_equal and both_hashable:
            assert hash(some_bidict) == hash(other)
        if b_has_eq_order_sens:
            are_equal_ordered = some_bidict.equals_order_sensitive(other)
            should_be_equal_ordered = OrderedDict(some_bidict) == OrderedDict(other)
            assert are_equal_ordered == should_be_equal_ordered

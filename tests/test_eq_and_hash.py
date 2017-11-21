# -*- coding: utf-8 -*-
# Copyright 2017 Joshua Bronson. All Rights Reserved.
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


# pylint: disable=C0103
items = [('a', 1), ('b', 2)]  # use int values so makes sense with Counter
itemsreversed = list(reversed(items))

bidict_of_items = bidict(items)
frozenbidict_of_items = frozenbidict(items)
namedbidict_of_items = namedbidict('named', 'keys', 'vals')(items)
orderedbidict_of_items = OrderedBidict(items)
orderedbidict_of_itemsreversed = OrderedBidict(itemsreversed)
orderedbidictsubcls_of_items = _OrderedBidictSubcls(items)
orderedbidictsubcls_of_itemsreversed = _OrderedBidictSubcls(itemsreversed)
frozenorderedbidict_of_items = FrozenOrderedBidict(items)
frozenorderedbidict_of_itemsreversed = FrozenOrderedBidict(itemsreversed)
bidicts = (
    bidict_of_items,
    frozenbidict_of_items,
    namedbidict_of_items,
    orderedbidict_of_items,
    orderedbidict_of_itemsreversed,
    orderedbidictsubcls_of_items,
    orderedbidictsubcls_of_itemsreversed,
    frozenorderedbidict_of_items,
    frozenorderedbidict_of_itemsreversed,
)

dict_of_itemsreversed = dict(itemsreversed)
counter_of_itemsreversed = Counter(dict_of_itemsreversed)
defaultdict_of_itemsreversed = defaultdict(lambda x: None, itemsreversed)
dictsubcls_of_itemsreversed = _DictSubcls(itemsreversed)
ordereddict_of_items = OrderedDict(items)
ordereddict_of_itemsreversed = OrderedDict(itemsreversed)
empty_dict = {}
not_a_mapping = 42
not_bidicts = (
    dict_of_itemsreversed,
    counter_of_itemsreversed,
    defaultdict_of_itemsreversed,
    dictsubcls_of_itemsreversed,
    ordereddict_of_items,
    ordereddict_of_itemsreversed,
    empty_dict,
    not_a_mapping,
)


@pytest.mark.parametrize('b, other', product(bidicts, bidicts + not_bidicts))
def test_eq_and_hash(b, other):
    """Make sure equality tests and hash results behave as expected."""
    if not isinstance(other, Mapping):
        assert b != other
    elif len(b) != len(other):
        assert b != other
    else:
        should_be_equal = dict(b) == dict(other)
        are_equal = b == other
        assert are_equal == should_be_equal
        both_hashable = isinstance(b, Hashable) and isinstance(other, Hashable)
        if are_equal and both_hashable:
            assert hash(b) == hash(other)

        if hasattr(b, 'equals_order_sensitive') and hasattr(other, '__reversed__'):
            are_equal_ordered = b.equals_order_sensitive(other)
            should_be_equal_ordered = OrderedDict(b) == OrderedDict(other)
            assert are_equal_ordered == should_be_equal_ordered

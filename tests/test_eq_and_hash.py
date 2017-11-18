# -*- coding: utf-8 -*-
# Copyright 2017 Joshua Bronson. All Rights Reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
Equality and hashing tests.
"""

from collections import Counter, Hashable, OrderedDict, Mapping, defaultdict
from itertools import product

import pytest
from bidict import FrozenOrderedBidict, OrderedBidict, bidict, namedbidict, frozenbidict
from bidict.compat import iteritems


# pylint: disable=C0111
class DictSubcls(dict):
    pass


class OrderedBidictSubcls(OrderedBidict):
    pass


# pylint: disable=C0103
items = [('a', 1), ('b', 2)]  # use int values so makes sense with Counter
itemsreversed = list(reversed(items))

bidict_of_items = bidict(items)
frozenbidict_of_items = frozenbidict(items)
namedbidict_of_items = namedbidict('named', 'keys', 'vals')(items)
orderedbidict_of_items = OrderedBidict(items)
orderedbidict_of_itemsreversed = OrderedBidict(itemsreversed)
orderedbidictsubcls_of_items = OrderedBidictSubcls(items)
orderedbidictsubcls_of_itemsreversed = OrderedBidictSubcls(itemsreversed)
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
dictsubcls_of_itemsreversed = DictSubcls(itemsreversed)
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


def _infer_compare_ordered(mapping):
    return getattr(mapping, '__reversed__', False) and mapping.__class__ is not dict


@pytest.mark.parametrize('b, other', product(bidicts, bidicts + not_bidicts))
def test_eq_and_hash(b, other):
    if not isinstance(other, Mapping):
        assert b != other
    elif len(b) != len(other):
        assert b != other
    else:
        should_compare_ordered = _infer_compare_ordered(b) and _infer_compare_ordered(other)
        delegate = OrderedDict if should_compare_ordered else dict
        should_be_equal = delegate(iteritems(b)) == delegate(iteritems(other))
        are_equal = b == other
        assert should_be_equal == are_equal
        if should_be_equal and isinstance(b, Hashable) and isinstance(other, Hashable):
            assert hash(b) == hash(other)

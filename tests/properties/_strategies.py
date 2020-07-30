# -*- coding: utf-8 -*-
# Copyright 2009-2020 Joshua Bronson. All Rights Reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Strategies for Hypothesis tests."""

from collections import OrderedDict
from operator import attrgetter, itemgetter
from os import getenv

import hypothesis.strategies as st
from bidict import DROP_NEW, DROP_OLD, RAISE, OnDup, OrderedBidictBase, namedbidict

from . import _types as t


MAX = int(getenv('HYPOTHESIS_GEN_MAX_SIZE', '0')) or None

BIDICT_TYPES = st.sampled_from(t.BIDICT_TYPES)
MUTABLE_BIDICT_TYPES = st.sampled_from(t.MUTABLE_BIDICT_TYPES)
FROZEN_BIDICT_TYPES = st.sampled_from(t.FROZEN_BIDICT_TYPES)
ORDERED_BIDICT_TYPES = st.sampled_from(t.ORDERED_BIDICT_TYPES)
MAPPING_TYPES = st.sampled_from(t.MAPPING_TYPES)
NON_BIDICT_MAPPING_TYPES = st.sampled_from(t.NON_BIDICT_MAPPING_TYPES)
ORDERED_MAPPING_TYPES = st.sampled_from(t.ORDERED_MAPPING_TYPES)
HASHABLE_MAPPING_TYPES = st.sampled_from(t.HASHABLE_MAPPING_TYPES)
ON_DUP_ACTIONS = st.sampled_from((DROP_NEW, DROP_OLD, RAISE))
ON_DUP = st.tuples(ON_DUP_ACTIONS, ON_DUP_ACTIONS, ON_DUP_ACTIONS).map(OnDup._make)

TEXT = st.text()
BOOLEANS = st.booleans()
ATOMS = st.none() | BOOLEANS | st.integers()
## Uncomment the following to mix in floats and text. Leaving commented out since it
## slows example generation without actually finding more falsifying examples.
# ATOMS != st.floats(allow_nan=False) | TEXT
NON_MAPPINGS = ATOMS | st.iterables(ATOMS)
HASHABLES = ATOMS
## Uncomment the following to mix in tuples (of tuples...) of ATOMS. Leaving commented
## out since it slows example generation without finding more falsifying examples.
# TUPLES = st.lists(ATOMS).map(tuple)
# TUPLES |= st.recursive(TUPLES, lambda i: st.lists(i).map(tuple))
# HASHABLES |= TUPLES
ODICTS_KW_PAIRS = st.dictionaries(TEXT, HASHABLES, dict_class=OrderedDict, max_size=MAX)
PAIRS = st.tuples(HASHABLES, HASHABLES)
L_PAIRS = st.lists(PAIRS, max_size=MAX)
I_PAIRS = st.iterables(PAIRS, max_size=MAX)
FST_SND = (itemgetter(0), itemgetter(1))
L_PAIRS_NODUP = st.lists(PAIRS, unique_by=FST_SND, max_size=MAX)
I_PAIRS_NODUP = st.iterables(PAIRS, unique_by=FST_SND, max_size=MAX)
DIFF_ITEMS = st.lists(L_PAIRS_NODUP.map(frozenset), min_size=2, max_size=2, unique=True)
SAME_ITEMS_DIFF_ORDER = st.tuples(
    st.lists(PAIRS, unique_by=FST_SND, min_size=2, max_size=MAX), st.randoms(use_true_random=False)
).map(
    lambda i: (i[0], i[1].sample(i[0], len(i[0])))  # (seq, shuffled seq)
).filter(lambda i: i[0] != i[1])


def _bidict_strat(bi_types, init_items=I_PAIRS_NODUP, _inv=attrgetter('inverse')):
    fwd_bidicts = st.tuples(bi_types, init_items).map(lambda i: i[0](i[1]))
    inv_bidicts = fwd_bidicts.map(_inv)
    return fwd_bidicts | inv_bidicts


BIDICTS = _bidict_strat(BIDICT_TYPES)
FROZEN_BIDICTS = _bidict_strat(FROZEN_BIDICT_TYPES)
MUTABLE_BIDICTS = _bidict_strat(MUTABLE_BIDICT_TYPES)
ORDERED_BIDICTS = _bidict_strat(ORDERED_BIDICT_TYPES)


_ALPHABET = [chr(i) for i in range(0x10ffff) if chr(i).isidentifier()]
_NAMEDBI_VALID_NAMES = st.text(_ALPHABET, min_size=1)
IS_VALID_NAME = str.isidentifier
NAMEDBIDICT_NAMES_ALL_VALID = st.lists(_NAMEDBI_VALID_NAMES, min_size=3, max_size=3, unique=True)
NAMEDBIDICT_NAMES_SOME_INVALID = st.lists(st.text(min_size=1), min_size=3, max_size=3).filter(
    lambda i: not all(IS_VALID_NAME(name) for name in i)
)
NAMEDBIDICT_TYPES = st.tuples(NAMEDBIDICT_NAMES_ALL_VALID, BIDICT_TYPES).map(
    lambda i: namedbidict(*i[0], base_type=i[1])
)
NAMEDBIDICTS = _bidict_strat(NAMEDBIDICT_TYPES)


def _bi_and_map(bi_types, map_types, init_items=L_PAIRS_NODUP):
    return st.tuples(bi_types, map_types, init_items).map(
        lambda i: (i[0](i[2]), i[1](i[2]))
    )


BI_AND_MAP_FROM_SAME_ITEMS = _bi_and_map(BIDICT_TYPES, MAPPING_TYPES)
OBI_AND_OD_FROM_SAME_ITEMS = _bi_and_map(ORDERED_BIDICT_TYPES, st.just(OrderedDict))
OBI_AND_OMAP_FROM_SAME_ITEMS = _bi_and_map(ORDERED_BIDICT_TYPES, ORDERED_MAPPING_TYPES)
HBI_AND_HMAP_FROM_SAME_ITEMS = _bi_and_map(FROZEN_BIDICT_TYPES, HASHABLE_MAPPING_TYPES)

_unpack = lambda i: (i[0](i[2][0]), i[1](i[2][1]))  # noqa: E731
BI_AND_MAP_FROM_DIFF_ITEMS = st.tuples(BIDICT_TYPES, MAPPING_TYPES, DIFF_ITEMS).map(_unpack)

OBI_AND_OMAP_FROM_SAME_ITEMS_DIFF_ORDER = st.tuples(
    ORDERED_BIDICT_TYPES, ORDERED_MAPPING_TYPES, SAME_ITEMS_DIFF_ORDER
).map(_unpack)

_cmpdict = lambda i: (OrderedDict if issubclass(i, OrderedBidictBase) else dict)  # noqa: E731

BI_AND_CMPDICT_FROM_SAME_ITEMS = st.tuples(BIDICT_TYPES, L_PAIRS_NODUP).map(
    lambda i: (i[0](i[1]), _cmpdict(i[0])(i[1]))
)

NO_ARGS = st.just(())
IM_ARG = st.tuples(HASHABLES)
IP_ARG = st.tuples(I_PAIRS)
TWO_IM_ARGS = st.tuples(HASHABLES, HASHABLES)

ARGS_BY_METHOD = st.fixed_dictionaries({
    # mutating
    # 0-arity
    (0, 'clear'): NO_ARGS,
    (0, 'popitem'): NO_ARGS,
    # 1-arity, an immutable atom
    (1, '__delitem__'): IM_ARG,
    (1, 'pop'): IM_ARG,
    (1, 'setdefault'): IM_ARG,
    (1, 'move_to_end'): IM_ARG,
    # 1-arity, a list of pairs
    (1, 'update'): IP_ARG,
    (1, 'forceupdate'): IP_ARG,
    # 2-arity
    (2, 'pop'): TWO_IM_ARGS,
    (2, 'setdefault'): TWO_IM_ARGS,
    (2, '__setitem__'): TWO_IM_ARGS,
    (2, 'put'): TWO_IM_ARGS,
    (2, 'forceput'): TWO_IM_ARGS,
    (2, 'move_to_end'): st.tuples(HASHABLES, BOOLEANS),
    # non-mutating
    # 0-arity
    (0, '__copy__'): NO_ARGS,
    (0, '__iter__'): NO_ARGS,
    (0, '__len__'): NO_ARGS,
    (0, 'copy'): NO_ARGS,
    (0, 'keys'): NO_ARGS,
    (0, 'items'): NO_ARGS,
    (0, 'values'): NO_ARGS,
    (0, 'iterkeys'): NO_ARGS,
    (0, 'iteritems'): NO_ARGS,
    (0, 'itervalues'): NO_ARGS,
    (0, 'viewkeys'): NO_ARGS,
    (0, 'viewitems'): NO_ARGS,
    (0, 'viewvalues'): NO_ARGS,
    # 1-arity
    (1, '__contains__'): IM_ARG,
    (1, '__getitem__'): IM_ARG,
    (1, 'get'): IM_ARG,
})

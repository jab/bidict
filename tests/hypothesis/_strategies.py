# -*- coding: utf-8 -*-
# Copyright 2009-2018 Joshua Bronson. All Rights Reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Strategies for Hypothesis tests."""

import re
from collections import OrderedDict

from hypothesis import assume, strategies as st
from bidict import IGNORE, OVERWRITE, RAISE, OrderedBidictBase, namedbidict
from bidict.compat import izip

import _types as t


# pylint: disable=invalid-name


DATA = st.data()
RAND = st.randoms()
BIDICT_TYPES = st.sampled_from(t.BIDICT_TYPES)
MUTABLE_BIDICT_TYPES = st.sampled_from(t.MUTABLE_BIDICT_TYPES)
FROZEN_BIDICT_TYPES = st.sampled_from(t.FROZEN_BIDICT_TYPES)
ORDERED_BIDICT_TYPES = st.sampled_from(t.ORDERED_BIDICT_TYPES)
MAPPING_TYPES = st.sampled_from(t.MAPPING_TYPES)
NON_BIDICT_MAPPING_TYPES = st.sampled_from(t.NON_BIDICT_MAPPING_TYPES)
ORDERED_MAPPING_TYPES = st.sampled_from(t.ORDERED_MAPPING_TYPES)
HASHABLE_MAPPING_TYPES = st.sampled_from(t.HASHABLE_MAPPING_TYPES)
DUP_POLICIES = st.sampled_from((IGNORE, OVERWRITE, RAISE))
DUP_POLICIES_DICT = st.fixed_dictionaries(dict(
    on_dup_key=DUP_POLICIES,
    on_dup_val=DUP_POLICIES,
    on_dup_kv=DUP_POLICIES,
))

BOOLEANS = st.booleans()
FLOATS = st.floats(allow_nan=False)
INTS = st.integers()
TEXT = st.text()
NONE = st.none()
IMMUTABLES = BOOLEANS | TEXT | NONE | INTS | FLOATS

LISTS_MAX_SIZE = 10
LISTS_PAIRS = st.lists(st.tuples(IMMUTABLES, IMMUTABLES), max_size=LISTS_MAX_SIZE)

NON_MAPPINGS = IMMUTABLES | LISTS_PAIRS


@st.composite
def _lists_pairs_with_duplication(draw):
    # pylint: disable=too-many-locals
    n = draw(st.integers(min_value=3, max_value=LISTS_MAX_SIZE))
    indexes = st.integers(min_value=0, max_value=n - 1)
    keys = draw(st.lists(IMMUTABLES, min_size=n, max_size=n))
    vals = draw(st.lists(IMMUTABLES, min_size=n, max_size=n))
    fwd = OrderedDict(izip(keys, vals))
    inv = OrderedDict(izip(vals, keys))
    which_to_dup = draw(RAND).choice((1, 2, 3))
    should_dup_key = which_to_dup in (1, 3)
    should_dup_val = which_to_dup in (2, 3)
    should_add_dup_key = should_dup_key and len(fwd) < n
    should_add_dup_val = should_dup_val and len(inv) < n
    if not should_add_dup_key and not should_add_dup_val:
        return list(izip(keys, vals))
    if should_add_dup_key:
        dup_key_idx = draw(indexes)
        added_key = keys[dup_key_idx]
    else:
        added_key = draw(IMMUTABLES)
        assume(added_key not in fwd)
    if should_add_dup_val:
        dup_val_idx = draw(indexes)
        if should_add_dup_key:
            assume(dup_val_idx != dup_key_idx)
        added_val = vals[dup_val_idx]
    else:
        added_val = draw(IMMUTABLES)
        assume(added_val not in inv)
    insert_idx = draw(indexes)
    keys.insert(insert_idx, added_key)
    vals.insert(insert_idx, added_val)
    return list(izip(keys, vals))


# pylint: disable=no-value-for-parameter
LISTS_PAIRS_DUP = _lists_pairs_with_duplication()


@st.composite
def lists_pairs_nodup(draw, elements=IMMUTABLES, min_size=0, max_size=LISTS_MAX_SIZE):
    """Generate a list of pairs from the given elements with no duplication."""
    n = draw(st.integers(min_value=min_size, max_value=max_size))
    size_n_sets = st.sets(elements, min_size=n, max_size=n)
    keys = draw(size_n_sets)
    vals = draw(size_n_sets)
    return list(izip(keys, vals))


LISTS_PAIRS_NODUP = lists_pairs_nodup()
LISTS_TEXT_PAIRS_NODUP = lists_pairs_nodup(elements=TEXT)


# pylint: disable=dangerous-default-value
@st.composite
def bidicts(draw, bi_types=BIDICT_TYPES, init_items=LISTS_PAIRS_NODUP):
    """Generate bidicts."""
    bi_cls = draw(bi_types)
    items = draw(init_items)
    bi = bi_cls(items)
    # Return the inverse bidict with 50% probability to increase coverage.
    return bi if draw(RAND).choice((True, False)) else bi.inv


BIDICTS = bidicts()
FROZEN_BIDICTS = bidicts(bi_types=FROZEN_BIDICT_TYPES)
MUTABLE_BIDICTS = bidicts(bi_types=MUTABLE_BIDICT_TYPES)
ORDERED_BIDICTS = bidicts(bi_types=ORDERED_BIDICT_TYPES)


NAMEDBIDICT_VALID_NAME_PAT = re.compile('[A-z][A-z0-9_]*$')
NAMEDBIDICT_NAMES = st.from_regex(NAMEDBIDICT_VALID_NAME_PAT, fullmatch=True)
NAMEDBIDICT_3_NAMES = st.tuples(
    NAMEDBIDICT_NAMES,
    NAMEDBIDICT_NAMES,
    NAMEDBIDICT_NAMES,
)


@st.composite
def _namedbidict_types(draw, names=NAMEDBIDICT_3_NAMES, base_types=BIDICT_TYPES):
    typename, keyname, valname = draw(names)
    assume(keyname != valname)
    base_type = draw(base_types)
    return namedbidict(typename, keyname, valname, base_type=base_type)


NAMEDBIDICT_TYPES = _namedbidict_types()


@st.composite
def _namedbidicts(draw, nb_types=NAMEDBIDICT_TYPES, init_items=LISTS_PAIRS_NODUP):
    nb_cls = draw(nb_types)
    items = draw(init_items)
    nb = nb_cls(items)
    # Return the inverse namedbidict with 50% probability to increase coverage.
    return nb if draw(RAND).choice((True, False)) else nb.inv


NAMEDBIDICTS = _namedbidicts()


_COMPARE_DICT_TYPE = object()
_SAME_AS_BI_ITEMS = object()
_SAME_AS_BI_ITEMS_DIFF_ORDER = object()


@st.composite
def _bidict_and_mapping_from_items(
        draw,
        bi_types=BIDICT_TYPES,
        map_types=MAPPING_TYPES,
        bi_items=LISTS_PAIRS_NODUP,
        map_items=_SAME_AS_BI_ITEMS,
):
    bi_cls = draw(bi_types)
    if map_types is _COMPARE_DICT_TYPE:
        map_cls = OrderedDict if issubclass(bi_cls, OrderedBidictBase) else dict
    else:
        map_cls = draw(map_types)
    bi_items_ = draw(bi_items)
    if map_items in (_SAME_AS_BI_ITEMS, _SAME_AS_BI_ITEMS_DIFF_ORDER):
        map_items_ = bi_items_[:]
        if map_items is _SAME_AS_BI_ITEMS_DIFF_ORDER:
            draw(RAND).shuffle(map_items_)
            assume(map_items_ != bi_items_)
    else:
        map_items_ = draw(map_items)
        assume(map_items_ != bi_items_)
    return bi_cls(bi_items_), map_cls(map_items_)


BIDICT_AND_MAPPING_FROM_SAME_ITEMS_NODUP = _bidict_and_mapping_from_items()
BIDICT_AND_MAPPING_FROM_DIFFERENT_ITEMS = _bidict_and_mapping_from_items(
    map_items=LISTS_PAIRS_NODUP,
)
BIDICT_AND_COMPARE_DICT_FROM_SAME_ITEMS_NODUP = _bidict_and_mapping_from_items(
    map_types=_COMPARE_DICT_TYPE,
)
ORDERED_BIDICT_AND_ORDERED_DICT_FROM_SAME_ITEMS_NODUP = _bidict_and_mapping_from_items(
    bi_types=ORDERED_BIDICT_TYPES,
    map_types=_COMPARE_DICT_TYPE,
)
ORDERED_BIDICT_AND_ORDERED_MAPPING_FROM_SAME_ITEMS_NODUP = _bidict_and_mapping_from_items(
    bi_types=ORDERED_BIDICT_TYPES,
    map_types=ORDERED_MAPPING_TYPES,
)
HASHABLE_BIDICT_AND_MAPPING_FROM_SAME_ITEMS_NODUP = _bidict_and_mapping_from_items(
    bi_types=FROZEN_BIDICT_TYPES,
    map_types=HASHABLE_MAPPING_TYPES,
)
ORDERED_BIDICT_AND_ORDERED_MAPPING_FROM_SAME_ITEMS_DIFF_ORDER = _bidict_and_mapping_from_items(
    bi_types=ORDERED_BIDICT_TYPES,
    map_types=ORDERED_MAPPING_TYPES,
    map_items=_SAME_AS_BI_ITEMS_DIFF_ORDER,
)


NO_ARGS = st.just(())
IM_ARG = st.tuples(IMMUTABLES)
LP_ARG = st.tuples(LISTS_PAIRS)
TWO_IM_ARGS = st.tuples(IMMUTABLES, IMMUTABLES)

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
    (1, 'update'): LP_ARG,
    (1, 'forceupdate'): LP_ARG,
    # 2-arity
    (2, 'pop'): TWO_IM_ARGS,
    (2, 'setdefault'): TWO_IM_ARGS,
    (2, '__setitem__'): TWO_IM_ARGS,
    (2, 'put'): TWO_IM_ARGS,
    (2, 'forceput'): TWO_IM_ARGS,
    (2, 'move_to_end'): st.tuples(IMMUTABLES, BOOLEANS),
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

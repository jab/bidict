# Copyright 2009-2023 Joshua Bronson. All rights reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Strategies for Hypothesis tests."""

from __future__ import annotations
from collections import OrderedDict
from operator import attrgetter, itemgetter, methodcaller
import typing as t

import hypothesis.strategies as st
from bidict import DROP_NEW, DROP_OLD, RAISE, OnDup, OrderedBidictBase, namedbidict

from . import _types as _t


def one_of(items: t.Any) -> t.Any:
    """Create a one_of strategy using the given items."""
    return st.one_of((st.just(i) for i in items))  # type: ignore [call-overload]


DATA = st.data()
BIDICT_TYPES = one_of(_t.BIDICT_TYPES)
MUTABLE_BIDICT_TYPES = one_of(_t.MUTABLE_BIDICT_TYPES)
FROZEN_BIDICT_TYPES = one_of(_t.FROZEN_BIDICT_TYPES)
ORDERED_BIDICT_TYPES = one_of(_t.ORDERED_BIDICT_TYPES)
REVERSIBLE_BIDICT_TYPES = one_of(_t.REVERSIBLE_BIDICT_TYPES)
MAPPING_TYPES = one_of(_t.MAPPING_TYPES)
NON_BI_MAPPING_TYPES = one_of(_t.NON_BI_MAPPING_TYPES)
NON_NAMED_BIDICT_TYPES = one_of(_t.NON_NAMED_BIDICT_TYPES)
ORDERED_MAPPING_TYPES = one_of(_t.ORDERED_MAPPING_TYPES)
HASHABLE_MAPPING_TYPES = one_of(_t.HASHABLE_MAPPING_TYPES)
ON_DUP_ACTIONS = one_of((DROP_NEW, DROP_OLD, RAISE))
ON_DUP = st.tuples(ON_DUP_ACTIONS, ON_DUP_ACTIONS, ON_DUP_ACTIONS).map(OnDup._make)

BOOLEANS = st.booleans()
# Combine a few different strategies together that generate atomic values
# that can be used to initialize test bidicts with. Including only None, bools, and ints
# provides enough coverage; including more just slows down example generation.
ATOMS = st.none() | BOOLEANS | st.integers()
PAIRS = st.tuples(ATOMS, ATOMS)
NON_MAPPINGS = ATOMS | st.iterables(ATOMS)
ALPHABET = tuple(chr(i) for i in range(0x10ffff) if chr(i).isidentifier())
VALID_NAMES = st.text(ALPHABET, min_size=1, max_size=16)
DICTS_KW_PAIRS = st.dictionaries(VALID_NAMES, ATOMS)
L_PAIRS = st.lists(PAIRS)
I_PAIRS = st.iterables(PAIRS)
FST_SND = (itemgetter(0), itemgetter(1))
L_PAIRS_NODUP = st.lists(PAIRS, unique_by=FST_SND)
I_PAIRS_NODUP = st.iterables(PAIRS, unique_by=FST_SND)
# Reserve a disjoint set of atoms as a source of values guaranteed not to have been
# inserted into a test bidict already.
DIFF_ATOMS = st.characters()
DIFF_PAIRS = st.tuples(DIFF_ATOMS, DIFF_ATOMS)
L_DIFF_PAIRS_NODUP = st.lists(DIFF_PAIRS, unique_by=FST_SND, min_size=1)
DIFF_ITEMS = st.tuples(L_PAIRS_NODUP, L_DIFF_PAIRS_NODUP)
RANDOMS = st.randoms(use_true_random=False)
SAME_ITEMS_DIFF_ORDER = st.tuples(
    st.lists(PAIRS, unique_by=FST_SND, min_size=2), RANDOMS
).map(
    lambda i: (i[0], i[1].sample(i[0], len(i[0])))  # (seq, shuffled seq)
).filter(lambda i: i[0] != i[1])


def _bidict_strat(bi_types: t.Any, init_items: t.Any = I_PAIRS_NODUP, _inv: t.Any = attrgetter('inverse')) -> t.Any:
    fwd_bidicts = st.tuples(bi_types, init_items).map(lambda i: i[0](i[1]))  # type: ignore
    inv_bidicts = fwd_bidicts.map(_inv)
    return fwd_bidicts | inv_bidicts


BIDICTS = _bidict_strat(BIDICT_TYPES)
FROZEN_BIDICTS = _bidict_strat(FROZEN_BIDICT_TYPES)
MUTABLE_BIDICTS = _bidict_strat(MUTABLE_BIDICT_TYPES)
ORDERED_BIDICTS = _bidict_strat(ORDERED_BIDICT_TYPES)

callkeys, callitems = methodcaller('keys'), methodcaller('items')
KEYSVIEW_SET_OP_ARGS = st.sets(ATOMS) | st.dictionaries(ATOMS, ATOMS).map(callkeys) | BIDICTS.map(callkeys)
ITEMSVIEW_SET_OP_ARGS = st.sets(PAIRS) | st.dictionaries(ATOMS, ATOMS).map(callitems) | BIDICTS.map(callitems)

NON_BI_MAPPINGS = st.tuples(NON_BI_MAPPING_TYPES, L_PAIRS).map(lambda i: i[0](i[1]))  # type: ignore


NAMEDBIDICT_NAMES_ALL_VALID = st.lists(VALID_NAMES, min_size=3, max_size=3, unique=True)
NAMEDBIDICT_NAMES_SOME_INVALID = st.lists(st.text(min_size=1), min_size=3, max_size=3).filter(
    lambda i: not all(str.isidentifier(name) for name in i)
)
NAMEDBIDICT_TYPES = st.tuples(NAMEDBIDICT_NAMES_ALL_VALID, NON_NAMED_BIDICT_TYPES).map(
    lambda i: namedbidict(*i[0], base_type=i[1])
)
NAMEDBIDICTS = _bidict_strat(NAMEDBIDICT_TYPES)


def _bi_and_map(bi_types: t.Any, map_types: t.Any = MAPPING_TYPES, init_items: t.Any = L_PAIRS_NODUP) -> t.Any:
    """Given bidict types and mapping types, return a pair of each type created from init_items."""
    return st.tuples(bi_types, map_types, init_items).map(
        lambda i: (i[0](i[2]), i[1](i[2]))
    )


BI_AND_MAP_FROM_SAME_ND_ITEMS = _bi_and_map(BIDICT_TYPES)
# Update the following when we drop support for Python < 3.8. On 3.8+, all mappings are reversible.
RBI_AND_RMAP_FROM_SAME_ND_ITEMS = _bi_and_map(REVERSIBLE_BIDICT_TYPES, st.just(OrderedDict))
HBI_AND_HMAP_FROM_SAME_ND_ITEMS = _bi_and_map(FROZEN_BIDICT_TYPES, HASHABLE_MAPPING_TYPES)

_unpack = lambda i: (i[0](i[2][0]), i[1](i[2][1]))  # noqa: E731
BI_AND_MAP_FROM_DIFF_ITEMS = st.tuples(BIDICT_TYPES, MAPPING_TYPES, DIFF_ITEMS).map(_unpack)

OBI_AND_OMAP_FROM_SAME_ITEMS_DIFF_ORDER = st.tuples(
    ORDERED_BIDICT_TYPES, ORDERED_MAPPING_TYPES, SAME_ITEMS_DIFF_ORDER
).map(_unpack)

_cmpdict: t.Any = lambda i: (OrderedDict if isinstance(i, OrderedBidictBase) else dict)  # noqa: E731
BI_AND_CMPDICT_FROM_SAME_ITEMS = L_PAIRS_NODUP.map(
    lambda items: (lambda b: (b, _cmpdict(b)(items)))(_bidict_strat(BIDICT_TYPES, items))
)

ARGS_ATOM = st.tuples(ATOMS)
ARGS_ITERPAIRS = st.tuples(I_PAIRS)
ARGS_ATOM_ATOM = st.tuples(ATOMS, ATOMS)

METHOD_ARGS_PAIRS = (
    # 0-arity methods -> no need to generate any args:
    ('clear', None),
    ('popitem', None),
    ('__copy__', None),
    ('__iter__', None),
    ('__len__', None),
    ('copy', None),
    ('keys', None),
    ('items', None),
    ('values', None),
    # 1-arity methods that take an atom:
    ('__contains__', ARGS_ATOM),
    ('__getitem__', ARGS_ATOM),
    ('__delitem__', ARGS_ATOM),
    ('get', ARGS_ATOM),
    ('pop', ARGS_ATOM),
    ('setdefault', ARGS_ATOM),
    ('move_to_end', ARGS_ATOM),
    # 1-arity methods that take an iterable of pairs:
    ('update', ARGS_ITERPAIRS),
    ('forceupdate', ARGS_ITERPAIRS),
    # 2-arity methods that take two atoms:
    ('__setitem__', ARGS_ATOM_ATOM),
    ('setdefault', ARGS_ATOM_ATOM),
    ('pop', ARGS_ATOM_ATOM),
    ('put', ARGS_ATOM_ATOM),
    ('forceput', ARGS_ATOM_ATOM),
    # Other
    ('popitem', st.tuples(BOOLEANS)),
    ('move_to_end', st.tuples(ATOMS, BOOLEANS)),
)

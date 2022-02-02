# Copyright 2009-2022 Joshua Bronson. All Rights Reserved.
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


def one_of(items):
    return st.one_of((st.just(i) for i in items))


DATA = st.data()
BIDICT_TYPES = one_of(t.BIDICT_TYPES)
MUTABLE_BIDICT_TYPES = one_of(t.MUTABLE_BIDICT_TYPES)
FROZEN_BIDICT_TYPES = one_of(t.FROZEN_BIDICT_TYPES)
ORDERED_BIDICT_TYPES = one_of(t.ORDERED_BIDICT_TYPES)
REVERSIBLE_BIDICT_TYPES = one_of(t.REVERSIBLE_BIDICT_TYPES)
MAPPING_TYPES = one_of(t.MAPPING_TYPES)
NON_BI_MAPPING_TYPES = one_of(t.NON_BI_MAPPING_TYPES)
ORDERED_MAPPING_TYPES = one_of(t.ORDERED_MAPPING_TYPES)
HASHABLE_MAPPING_TYPES = one_of(t.HASHABLE_MAPPING_TYPES)
ON_DUP_ACTIONS = one_of((DROP_NEW, DROP_OLD, RAISE))
ON_DUP = st.tuples(ON_DUP_ACTIONS, ON_DUP_ACTIONS, ON_DUP_ACTIONS).map(OnDup._make)

TEXT = st.text()
BOOLEANS = st.booleans()
# Combine a few different strategies together that generate atomic values
# that can be used to initialize test bidicts with. Including only None, bools, and ints
# provides enough coverage; including more just slows down example generation.
ATOMS = st.none() | BOOLEANS | st.integers()
PAIRS = st.tuples(ATOMS, ATOMS)
SETS = st.sets(ATOMS)
SETS_PAIRS = st.sets(PAIRS)
NON_MAPPINGS = ATOMS | st.iterables(ATOMS)
ODICTS_KW_PAIRS = st.dictionaries(TEXT, ATOMS, dict_class=OrderedDict, max_size=MAX)
L_PAIRS = st.lists(PAIRS, max_size=MAX)
I_PAIRS = st.iterables(PAIRS, max_size=MAX)
FST_SND = (itemgetter(0), itemgetter(1))
L_PAIRS_NODUP = st.lists(PAIRS, unique_by=FST_SND, max_size=MAX)
I_PAIRS_NODUP = st.iterables(PAIRS, unique_by=FST_SND, max_size=MAX)
# Reserve a disjoint set of atoms as a source of values guaranteed not to have been
# inserted into a test bidict already.
DIFF_ATOMS = st.characters()
DIFF_PAIRS = st.tuples(DIFF_ATOMS, DIFF_ATOMS)
L_DIFF_PAIRS_NODUP = st.lists(DIFF_PAIRS, unique_by=FST_SND, min_size=1, max_size=MAX)
DIFF_ITEMS = st.tuples(L_PAIRS_NODUP, L_DIFF_PAIRS_NODUP)
RANDOMS = st.randoms(use_true_random=False)
SAME_ITEMS_DIFF_ORDER = st.tuples(
    st.lists(PAIRS, unique_by=FST_SND, min_size=2, max_size=MAX), RANDOMS
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

NON_BI_MAPPINGS = st.tuples(NON_BI_MAPPING_TYPES, L_PAIRS).map(lambda i: i[0](i[1]))


_ALPHABET = tuple(chr(i) for i in range(0x10ffff) if chr(i).isidentifier())
_NAMEDBI_VALID_NAMES = st.text(_ALPHABET, min_size=1)
NAMEDBIDICT_NAMES_ALL_VALID = st.lists(_NAMEDBI_VALID_NAMES, min_size=3, max_size=3, unique=True)
NAMEDBIDICT_NAMES_SOME_INVALID = st.lists(st.text(min_size=1), min_size=3, max_size=3).filter(
    lambda i: not all(str.isidentifier(name) for name in i)
)
NAMEDBIDICT_TYPES = st.tuples(NAMEDBIDICT_NAMES_ALL_VALID, BIDICT_TYPES).map(
    lambda i: namedbidict(*i[0], base_type=i[1])
)
NAMEDBIDICTS = _bidict_strat(NAMEDBIDICT_TYPES)


def _bi_and_map(bi_types, map_types=MAPPING_TYPES, init_items=L_PAIRS_NODUP):
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

_cmpdict = lambda i: (OrderedDict if isinstance(i, OrderedBidictBase) else dict)  # noqa: E731
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

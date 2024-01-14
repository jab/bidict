# Copyright 2009-2024 Joshua Bronson. All rights reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Microbenchmarks.

Uses https://pytest-benchmark.readthedocs.io/en/v4.0.0/pedantic.html
which pairs well with ../cachegrind.py (as used by ../.github/workflows/benchmark.yml).
"""

from __future__ import annotations

import pickle
import typing as t
from collections import deque
from functools import partial

import pytest

import bidict


consume: t.Any = partial(deque, maxlen=0)
LENS = (99, 999, 9_999)
DICTS_BY_LEN = {n: {i: i for i in range(n)} for n in LENS}
BIDICTS_BY_LEN = {n: bidict.bidict(DICTS_BY_LEN[n]) for n in LENS}
ORDERED_BIDICTS_BY_LEN = {n: bidict.OrderedBidict(DICTS_BY_LEN[n]) for n in LENS}
DICTS_BY_LEN_LAST_ITEM_DUPVAL = {n: {**DICTS_BY_LEN[n], n - 1: 0} for n in LENS}

BIDICT_AND_DICT_ONLY_LAST_ITEM_DIFFERENT = {n: (BIDICTS_BY_LEN[n], DICTS_BY_LEN_LAST_ITEM_DUPVAL[n]) for n in LENS}

ORDERED_BIDICT_AND_DICT_ONLY_LAST_ITEM_DIFFERENT = {
    n: (bidict.OrderedBidict(bi_and_d[0]), bi_and_d[1])
    for (n, bi_and_d) in BIDICT_AND_DICT_ONLY_LAST_ITEM_DIFFERENT.items()
}

BIDICT_AND_DICT_LAST_TWO_ITEMS_DIFFERENT_ORDER = {}
ORDERED_BIDICT_AND_DICT_LAST_TWO_ITEMS_DIFFERENT_ORDER = {}
for _i in LENS:
    _bi = BIDICTS_BY_LEN[_i]
    _d = dict(_bi)
    _last, _secondlast = _d.popitem(), _d.popitem()
    _d[_last[0]] = _last[1]  # new second-last
    _d[_secondlast[0]] = _secondlast[1]  # new last
    BIDICT_AND_DICT_LAST_TWO_ITEMS_DIFFERENT_ORDER[_i] = (_bi, _d)
    ORDERED_BIDICT_AND_DICT_LAST_TWO_ITEMS_DIFFERENT_ORDER[_i] = (bidict.OrderedBidict(_bi), _d)


@pytest.mark.parametrize('n', LENS)
def test_bi_init_from_dict(n: int, benchmark: t.Any) -> None:
    """Benchmark initializing a new bidict from a dict."""
    other = DICTS_BY_LEN[n]
    benchmark.pedantic(bidict.bidict, args=(other,))


@pytest.mark.parametrize('n', LENS)
def test_bi_init_from_bi(n: int, benchmark: t.Any) -> None:
    """Benchmark initializing a bidict from another bidict."""
    other = BIDICTS_BY_LEN[n]
    benchmark.pedantic(bidict.bidict, args=(other,))


@pytest.mark.parametrize('n', LENS)
def test_bi_init_fail_worst_case(n: int, benchmark: t.Any) -> None:
    """Benchmark initializing a bidict from a dict with a final duplicate value."""
    other = DICTS_BY_LEN_LAST_ITEM_DUPVAL[n]

    def failing_init() -> None:
        with pytest.raises(bidict.DuplicationError):
            bidict.bidict(other)

    benchmark.pedantic(failing_init)


@pytest.mark.parametrize('n', LENS)
def test_empty_bi_update_from_bi(n: int, benchmark: t.Any) -> None:
    """Benchmark updating an empty bidict from another bidict."""
    bi: bidict.bidict[int, int] = bidict.bidict()
    other = BIDICTS_BY_LEN[n]
    benchmark.pedantic(bi.update, args=(other,))
    assert bi == other


@pytest.mark.parametrize('n', LENS)
def test_small_bi_update_from_bi(n: int, benchmark: t.Any) -> None:
    """Benchmark updating a small bidict from another bidict that has no duplication."""
    bi = bidict.bidict({i: i for i in range(-9, 0)})
    other = BIDICTS_BY_LEN[n]
    benchmark.pedantic(bi.update, args=(other,))
    assert bi.keys() == set(range(-9, 0)) | other.keys()


@pytest.mark.parametrize('n', LENS)
def test_small_bi_large_update_fails_worst_case(n: int, benchmark: t.Any) -> None:
    """Benchmark updating a small bidict with a large update that fails on the final item and then rolls back."""
    bi = bidict.bidict({i: i for i in range(-9, 0)})
    other = DICTS_BY_LEN_LAST_ITEM_DUPVAL[n]

    def failing_update() -> None:
        with pytest.raises(bidict.DuplicationError):
            bi.update(other)

    benchmark.pedantic(failing_update)
    assert list(bi.items()) == [(i, i) for i in range(-9, 0)]


@pytest.mark.parametrize('n', LENS)
def test_bi_iter(n: int, benchmark: t.Any) -> None:
    """Benchmark iterating over a bidict."""
    bi = BIDICTS_BY_LEN[n]
    benchmark.pedantic(consume, args=(iter(bi),))


@pytest.mark.parametrize('n', LENS)
def test_orderedbi_iter(n: int, benchmark: t.Any) -> None:
    """Benchmark iterating over an OrderedBidict."""
    ob = ORDERED_BIDICTS_BY_LEN[n]
    benchmark.pedantic(consume, args=(iter(ob),))


@pytest.mark.parametrize('n', LENS)
def test_bi_contains_key_present(n: int, benchmark: t.Any) -> None:
    """Benchmark bidict.__contains__ with a contained key."""
    bi = BIDICTS_BY_LEN[n]
    key = next(iter(bi))
    result = benchmark.pedantic(bi.__contains__, args=(key,))
    assert result


@pytest.mark.parametrize('n', LENS)
def test_bi_contains_key_missing(n: int, benchmark: t.Any) -> None:
    """Benchmark bidict.__contains__ with a missing key."""
    bi = BIDICTS_BY_LEN[n]
    result = benchmark.pedantic(bi.__contains__, args=(object(),))
    assert not result


@pytest.mark.parametrize('n', LENS)
def test_bi_equals_with_equal_dict(n: int, benchmark: t.Any) -> None:
    """Benchmark bidict.__eq__ with an equivalent dict."""
    bi, d = BIDICT_AND_DICT_LAST_TWO_ITEMS_DIFFERENT_ORDER[n]
    result = benchmark.pedantic(bi.__eq__, args=(d,))
    assert result


@pytest.mark.parametrize('n', LENS)
def test_orderedbi_equals_with_equal_dict(n: int, benchmark: t.Any) -> None:
    """Benchmark OrderedBidict.__eq__ with an equivalent dict."""
    ob, d = ORDERED_BIDICT_AND_DICT_LAST_TWO_ITEMS_DIFFERENT_ORDER[n]
    result = benchmark.pedantic(ob.__eq__, args=(d,))
    assert result


@pytest.mark.parametrize('n', LENS)
def test_orderedbi_items_equals_with_equal_dict_items(n: int, benchmark: t.Any) -> None:
    """Benchmark OrderedBidict.items().__eq__ with an equivalent dict_items."""
    ob, d = ORDERED_BIDICT_AND_DICT_LAST_TWO_ITEMS_DIFFERENT_ORDER[n]
    obi, di = ob.items(), d.items()
    result = benchmark.pedantic(obi.__eq__, args=(di,))
    assert result


@pytest.mark.parametrize('n', LENS)
def test_orderedbi_items_equals_with_unequal_dict_items(n: int, benchmark: t.Any) -> None:
    """Benchmark OrderedBidict.items().__eq__ with an unequal dict_items."""
    ob, d = ORDERED_BIDICT_AND_DICT_ONLY_LAST_ITEM_DIFFERENT[n]
    obi, di = ob.items(), d.items()
    result = benchmark.pedantic(obi.__eq__, args=(di,))
    assert not result


@pytest.mark.parametrize('n', LENS)
def test_bi_equals_with_unequal_dict(n: int, benchmark: t.Any) -> None:
    """Benchmark bidict.__eq__ with an unequal dict."""
    bi, d = BIDICT_AND_DICT_ONLY_LAST_ITEM_DIFFERENT[n]
    result = benchmark.pedantic(bi.__eq__, args=(d,))
    assert not result


@pytest.mark.parametrize('n', LENS)
def test_orderedbi_equals_with_unequal_dict(n: int, benchmark: t.Any) -> None:
    """Benchmark OrderedBidict.__eq__ with an unequal dict."""
    ob, d = ORDERED_BIDICT_AND_DICT_ONLY_LAST_ITEM_DIFFERENT[n]
    result = benchmark.pedantic(ob.__eq__, args=(d,))
    assert not result


@pytest.mark.parametrize('n', LENS)
def test_bi_order_sensitive_equals_dict(n: int, benchmark: t.Any) -> None:
    """Benchmark bidict.equals_order_sensitive with an order-sensitive-equal dict."""
    bi, d = BIDICTS_BY_LEN[n], DICTS_BY_LEN[n]
    result = benchmark.pedantic(bi.equals_order_sensitive, args=(d,))
    assert result


@pytest.mark.parametrize('n', LENS)
def test_orderedbi_order_sensitive_equals_dict(n: int, benchmark: t.Any) -> None:
    """Benchmark OrderedBidict.equals_order_sensitive with an order-sensitive-equal dict."""
    ob, d = ORDERED_BIDICTS_BY_LEN[n], DICTS_BY_LEN[n]
    result = benchmark.pedantic(ob.equals_order_sensitive, args=(d,))
    assert result


@pytest.mark.parametrize('n', LENS)
def test_bi_equals_order_sensitive_with_unequal_dict(n: int, benchmark: t.Any) -> None:
    """Benchmark bidict.equals_order_sensitive with an order-sensitive-unequal dict."""
    bi, d = BIDICT_AND_DICT_LAST_TWO_ITEMS_DIFFERENT_ORDER[n]
    result = benchmark.pedantic(bi.equals_order_sensitive, args=(d,))
    assert not result


@pytest.mark.parametrize('n', LENS)
def test_orderedbi_equals_order_sensitive_with_unequal_dict(n: int, benchmark: t.Any) -> None:
    """Benchmark OrderedBidict.equals_order_sensitive with an order-sensitive-unequal dict."""
    ob, d = ORDERED_BIDICT_AND_DICT_LAST_TWO_ITEMS_DIFFERENT_ORDER[n]
    result = benchmark.pedantic(ob.equals_order_sensitive, args=(d,))
    assert not result


@pytest.mark.parametrize('n', LENS)
def test_copy(n: int, benchmark: t.Any) -> None:
    """Benchmark creating a copy of a bidict."""
    bi = BIDICTS_BY_LEN[n]
    benchmark.pedantic(bi.copy)


@pytest.mark.parametrize('n', LENS)
def test_pickle(n: int, benchmark: t.Any) -> None:
    """Benchmark pickling a bidict."""
    bi = BIDICTS_BY_LEN[n]
    benchmark.pedantic(pickle.dumps, args=(bi,))


@pytest.mark.parametrize('n', LENS)
def test_unpickle(n: int, benchmark: t.Any) -> None:
    """Benchmark unpickling a bidict."""
    bp = pickle.dumps(BIDICTS_BY_LEN[n])
    benchmark.pedantic(pickle.loads, args=(bp,))

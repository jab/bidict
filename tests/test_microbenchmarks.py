# Copyright 2009-2022 Joshua Bronson. All Rights Reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Microbenchmarks."""

import pickle
import sys
import typing as t
from collections import deque
from functools import partial

import pytest

import bidict as b


consume = partial(deque, maxlen=0)


def make_items(n: int) -> t.Iterable[t.Tuple[t.Any, t.Any]]:
    """As in:
    >>> tuple(make_items(3))
    ((0, 0), (1, 1), (2, 2))
    """
    return zip(range(n), range(n))


LENS = (99, 999, 9_999, 99_999)
DICTS_BY_LEN = {n: dict(make_items(n)) for n in LENS}
BIDICTS_BY_LEN = {n: b.bidict(DICTS_BY_LEN[n]) for n in LENS}
ORDERED_BIDICTS_BY_LEN = {n: b.OrderedBidict(DICTS_BY_LEN[n]) for n in LENS}
SMALL_BIDICT = b.bidict(zip(range(-9, 0), range(-9, 0)))
DICTS_BY_LEN_LAST_ITEM_DUPVAL = {n: {**DICTS_BY_LEN[n], **{n - 1: 0}} for n in LENS}
if sys.version_info >= (3, 8):  # dicts support reversed
    _checkd = next(iter(DICTS_BY_LEN_LAST_ITEM_DUPVAL.values()))
    _lastk, _lastv = next(reversed(_checkd.items()))
    _firstk, _firstv = next(iter(_checkd.items()))
    assert _firstk != _lastk and _firstv == _lastv

BIDICT_AND_DICT_ONLY_LAST_ITEM_DIFFERENT = {
    n: (BIDICTS_BY_LEN[n], DICTS_BY_LEN_LAST_ITEM_DUPVAL[n])
    for n in LENS
}
_checkbi, _checkd = next(iter(BIDICT_AND_DICT_ONLY_LAST_ITEM_DIFFERENT.values()))
assert _checkbi != _checkd
assert tuple(_checkbi.items())[:-1] == tuple(_checkd.items())[:-1]

ORDERED_BIDICT_AND_DICT_ONLY_LAST_ITEM_DIFFERENT = {
    n: (b.OrderedBidict(bi_and_d[0]), bi_and_d[1])
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
    ORDERED_BIDICT_AND_DICT_LAST_TWO_ITEMS_DIFFERENT_ORDER[_i] = (b.OrderedBidict(_bi), _d)


@pytest.mark.parametrize('n', LENS)
def test_bi_init_from_dict(n, benchmark):
    """Benchmark initializing a new bidict from a dictionary."""
    other = DICTS_BY_LEN[n]
    benchmark(b.bidict, other)


@pytest.mark.parametrize('n', LENS)
def test_bi_init_from_bi(n, benchmark):
    """Benchmark initializing a bidict from another bidict."""
    other = BIDICTS_BY_LEN[n]
    benchmark(b.bidict, other)


@pytest.mark.parametrize('n', LENS)
def test_bi_init_fail_worst_case(n, benchmark):
    """Benchmark initializing a bidict from a dict with a final duplicate value."""
    other = DICTS_BY_LEN_LAST_ITEM_DUPVAL[n]

    def expect_failing_init():
        try:
            b.bidict(other)
        except b.DuplicationError:
            pass
        else:
            raise Exception('Expected DuplicationError')

    benchmark(expect_failing_init)


@pytest.mark.parametrize('n', LENS)
def test_empty_bi_update_from_bi(n, benchmark):
    """Benchmark updating an empty bidict from another bidict."""
    bi = b.bidict()
    other = BIDICTS_BY_LEN[n]
    benchmark(lambda: bi.update(other))
    assert dict(bi) == other


@pytest.mark.parametrize('n', LENS)
def test_small_bi_large_update_fails_worst_case(n, benchmark):
    """Benchmark updating a small bidict with a large update that fails on the final item and then rolls back."""
    other = DICTS_BY_LEN_LAST_ITEM_DUPVAL[n]
    check = SMALL_BIDICT.copy()
    expect = SMALL_BIDICT.copy()

    def apply_failing_update():
        try:
            check.update(other)
        except b.DuplicationError:
            pass  # Rollback should happen here.
        else:
            raise Exception('Expected DuplicationError')

    benchmark(apply_failing_update)
    assert dict(check) == dict(expect), 'Update did not roll back'


@pytest.mark.parametrize('n', LENS)
def test_bi_iter(n, benchmark):
    """Benchmark iterating over a bidict."""
    bi = BIDICTS_BY_LEN[n]
    benchmark(consume, iter(bi))


@pytest.mark.parametrize('n', LENS)
def test_orderedbi_iter(n, benchmark):
    """Benchmark iterating over an OrderedBidict."""
    ob = ORDERED_BIDICTS_BY_LEN[n]
    benchmark(consume, iter(ob))


@pytest.mark.parametrize('n', LENS)
def test_bi_contains_key_present(n, benchmark):
    """Benchmark calling bidict.__contains__ with a contained key."""
    bi = BIDICTS_BY_LEN[n]
    key = next(iter(bi))
    result = benchmark(bi.__contains__, key)
    assert result


@pytest.mark.parametrize('n', LENS)
def test_bi_contains_key_missing(n, benchmark):
    """Benchmark calling bidict.__contains__ with a missing key."""
    bi = BIDICTS_BY_LEN[n]
    result = benchmark(bi.__contains__, object())
    assert not result


@pytest.mark.parametrize('n', LENS)
def test_bi_equals_equivalent_dict_worst_case(n, benchmark):
    """Benchmark calling bidict.__eq__ with an equivalent dict whose order is slightly different."""
    bi, d = BIDICT_AND_DICT_LAST_TWO_ITEMS_DIFFERENT_ORDER[n]
    result = benchmark(bi.__eq__, d)
    assert result


@pytest.mark.parametrize('n', LENS)
def test_orderedbi_equals_equivalent_dict_worst_case(n, benchmark):
    """Benchmark calling OrderedBidict.__eq__ with an equivalent dict whose order is slightly different."""
    ob, d = ORDERED_BIDICT_AND_DICT_LAST_TWO_ITEMS_DIFFERENT_ORDER[n]
    result = benchmark(ob.__eq__, d)
    assert result


@pytest.mark.parametrize('n', LENS)
def test_orderedbi_items_equals_equivalent_dict_items_worst_case(n, benchmark):
    """Benchmark calling OrderedBidict.items().__eq__ with an equivalent dict.items() whose order is slightly different."""
    ob, d = ORDERED_BIDICT_AND_DICT_LAST_TWO_ITEMS_DIFFERENT_ORDER[n]
    obi, di = ob.items(), d.items()
    result = benchmark(obi.__eq__, di)
    assert result


@pytest.mark.parametrize('n', LENS)
def test_bi_not_equals_dict_worst_case(n, benchmark):
    """Benchmark calling bidict.__eq__ with an unequal dict that differs only in its last item."""
    bi, d = BIDICT_AND_DICT_ONLY_LAST_ITEM_DIFFERENT[n]
    result = benchmark(bi.__eq__, d)
    assert not result


@pytest.mark.parametrize('n', LENS)
def test_orderedbi_not_equals_dict_worst_case(n, benchmark):
    """Benchmark calling OrderedBidict.__eq__ with an unequal dict that differs only in its last item."""
    ob, d = ORDERED_BIDICT_AND_DICT_ONLY_LAST_ITEM_DIFFERENT[n]
    result = benchmark(ob.__eq__, d)
    assert not result


@pytest.mark.parametrize('n', LENS)
def test_bi_order_sensitive_equals_dict(n, benchmark):
    """Benchmark calling bidict.equals_order_sensitive with an order-sensitive-equal dict."""
    bi, d = BIDICTS_BY_LEN[n], DICTS_BY_LEN[n]
    result = benchmark(bi.equals_order_sensitive, d)
    assert result


@pytest.mark.parametrize('n', LENS)
def test_orderedbi_order_sensitive_equals_dict(n, benchmark):
    """Benchmark calling OrderedBidict.equals_order_sensitive with an order-sensitive-equal dict."""
    ob, d = ORDERED_BIDICTS_BY_LEN[n], DICTS_BY_LEN[n]
    result = benchmark(ob.equals_order_sensitive, d)
    assert result


@pytest.mark.parametrize('n', LENS)
def test_bi_order_sensitive_not_equals_dict_worst_case(n, benchmark):
    bi, d = BIDICT_AND_DICT_LAST_TWO_ITEMS_DIFFERENT_ORDER[n]
    result = benchmark(bi.equals_order_sensitive, d)
    assert not result


@pytest.mark.parametrize('n', LENS)
def test_orderedbi_order_sensitive_not_equals_dict_worst_case(n, benchmark):
    ob, d = ORDERED_BIDICT_AND_DICT_LAST_TWO_ITEMS_DIFFERENT_ORDER[n]
    result = benchmark(ob.equals_order_sensitive, d)
    assert not result


@pytest.mark.parametrize('n', LENS)
def test_copy(n, benchmark):
    """Benchmark creating a copy of a bidict."""
    bi = BIDICTS_BY_LEN[n]
    benchmark(bi.copy)


@pytest.mark.parametrize('n', LENS)
def test_pickle(n, benchmark):
    """Benchmark pickling a bidict."""
    bi = BIDICTS_BY_LEN[n]
    benchmark(pickle.dumps, bi)


@pytest.mark.parametrize('n', LENS)
def test_unpickle(n, benchmark):
    """Benchmark unpickling a bidict."""
    bp = pickle.dumps(BIDICTS_BY_LEN[n])
    benchmark(pickle.loads, bp)

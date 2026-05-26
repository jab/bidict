# Copyright 2009-2026 Joshua Bronson. All rights reserved.
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
LENS = (100, 1_000, 10_000)
DATASET_NAMES = ('int', 'str')


INT_DICTS_BY_LEN: dict[int, dict[int, int]] = {n: {i: i for i in range(n)} for n in LENS}
STR_DICTS_BY_LEN: dict[int, dict[str, str]] = {n: {f'key{i}': f'value{i}' for i in range(n)} for n in LENS}
DICTS_BY_KIND_AND_LEN: dict[str, dict[int, dict[t.Any, t.Any]]] = {
    'int': INT_DICTS_BY_LEN,
    'str': STR_DICTS_BY_LEN,
}
BIDICTS_BY_KIND_AND_LEN: dict[str, dict[int, bidict.bidict[t.Any, t.Any]]] = {
    kind: {n: bidict.bidict(other) for n, other in dicts_by_len.items()}
    for kind, dicts_by_len in DICTS_BY_KIND_AND_LEN.items()
}
LOOKUP_ITEMS_BY_KIND_AND_LEN: dict[str, dict[int, tuple[t.Any, t.Any]]] = {
    kind: {n: next(iter(other.items())) for n, other in dicts_by_len.items()}
    for kind, dicts_by_len in DICTS_BY_KIND_AND_LEN.items()
}

INT_BIDICTS_BY_LEN: dict[int, bidict.bidict[int, int]] = t.cast(
    'dict[int, bidict.bidict[int, int]]',
    BIDICTS_BY_KIND_AND_LEN['int'],
)
ORDERED_BIDICTS_BY_LEN: dict[int, bidict.OrderedBidict[int, int]] = {
    n: bidict.OrderedBidict(INT_DICTS_BY_LEN[n]) for n in LENS
}

INT_DICTS_BY_LEN_DUPVAL_EARLY: dict[int, dict[int, int]] = {
    n: dict([(0, 0), (1, 0), *((i, i) for i in range(2, n))]) for n in LENS
}
INT_DICTS_BY_LEN_DUPVAL_LATE: dict[int, dict[int, int]] = {n: {**INT_DICTS_BY_LEN[n], n - 1: 0} for n in LENS}

SETITEM_NEW_ARGS_BY_LEN: dict[int, tuple[int, int]] = {n: (-1, -1) for n in LENS}
SETITEM_NEW_RESULTS_BY_LEN: dict[int, dict[int, int]] = {n: (INT_DICTS_BY_LEN[n] | {-1: -1}) for n in LENS}

SETITEM_REPLACE_ARGS_BY_LEN: dict[int, tuple[int, int]] = {n: (n - 1, -1) for n in LENS}
SETITEM_REPLACE_RESULTS_BY_LEN: dict[int, dict[int, int]] = {n: (INT_DICTS_BY_LEN[n] | {n - 1: -1}) for n in LENS}

FORCEPUT_ARGS_BY_LEN: dict[int, tuple[int, int]] = {n: (-1, 0) for n in LENS}
FORCEPUT_RESULTS_BY_LEN: dict[int, dict[int, int]] = {
    n: ({k: v for k, v in INT_DICTS_BY_LEN[n].items() if k != 0} | {-1: 0}) for n in LENS
}

POP_ARGS_BY_LEN: dict[int, tuple[int, int]] = {n: (n - 1, n - 1) for n in LENS}
POP_RESULTS_BY_LEN: dict[int, dict[int, int]] = {
    n: {k: v for k, v in INT_DICTS_BY_LEN[n].items() if k != n - 1} for n in LENS
}

PARTIAL_OVERLAP_UPDATES_BY_LEN: dict[int, dict[int, int]] = {
    n: {i: i for i in range(n // 2, n + (n // 2))} for n in LENS
}
PARTIAL_OVERLAP_RESULTS_BY_LEN: dict[int, dict[int, int]] = {
    n: (INT_DICTS_BY_LEN[n] | PARTIAL_OVERLAP_UPDATES_BY_LEN[n]) for n in LENS
}

BIDICT_AND_DICT_LAST_TWO_ITEMS_DIFFERENT_ORDER: dict[int, tuple[bidict.bidict[int, int], dict[int, int]]] = {}
ORDERED_BIDICT_AND_DICT_LAST_TWO_ITEMS_DIFFERENT_ORDER: dict[
    int, tuple[bidict.OrderedBidict[int, int], dict[int, int]]
] = {}
for _i in LENS:
    _bi = INT_BIDICTS_BY_LEN[_i]
    _d = dict(_bi)
    _last, _secondlast = _d.popitem(), _d.popitem()
    _d[_last[0]] = _last[1]  # new second-last
    _d[_secondlast[0]] = _secondlast[1]  # new last
    BIDICT_AND_DICT_LAST_TWO_ITEMS_DIFFERENT_ORDER[_i] = (_bi, _d)
    ORDERED_BIDICT_AND_DICT_LAST_TWO_ITEMS_DIFFERENT_ORDER[_i] = (
        bidict.OrderedBidict(_bi),
        _d,
    )


def _setitem(bi: bidict.bidict[int, int], key: int, val: int, _expected: dict[int, int]) -> None:
    bi[key] = val


def _forceput(bi: bidict.bidict[int, int], key: int, val: int, _expected: dict[int, int]) -> None:
    bi.forceput(key, val)


def _update(bi: bidict.bidict[int, int], other: dict[int, int], _expected: dict[int, int]) -> None:
    bi.update(other)


def _failing_update(bi: bidict.bidict[int, int], other: dict[int, int], _expected: dict[int, int]) -> None:
    with pytest.raises(bidict.DuplicationError):
        bi.update(other)


def _pop(bi: bidict.bidict[int, int], key: int, _expected_val: int, _expected: dict[int, int]) -> int:
    return bi.pop(key)


def _assert_mapping_matches(*args: t.Any) -> None:
    assert dict(args[0]) == args[-1]


def _setup_setitem_new(n: int) -> tuple[tuple[t.Any, ...], dict[str, t.Any]]:
    key, val = SETITEM_NEW_ARGS_BY_LEN[n]
    return (
        (INT_BIDICTS_BY_LEN[n].copy(), key, val, SETITEM_NEW_RESULTS_BY_LEN[n]),
        {},
    )


def _setup_setitem_replace_existing_key(n: int) -> tuple[tuple[t.Any, ...], dict[str, t.Any]]:
    key, val = SETITEM_REPLACE_ARGS_BY_LEN[n]
    return (
        (
            INT_BIDICTS_BY_LEN[n].copy(),
            key,
            val,
            SETITEM_REPLACE_RESULTS_BY_LEN[n],
        ),
        {},
    )


def _setup_forceput_existing_value(n: int) -> tuple[tuple[t.Any, ...], dict[str, t.Any]]:
    key, val = FORCEPUT_ARGS_BY_LEN[n]
    return (
        (INT_BIDICTS_BY_LEN[n].copy(), key, val, FORCEPUT_RESULTS_BY_LEN[n]),
        {},
    )


def _setup_pop(n: int) -> tuple[tuple[t.Any, ...], dict[str, t.Any]]:
    key, expected_val = POP_ARGS_BY_LEN[n]
    return (
        (
            INT_BIDICTS_BY_LEN[n].copy(),
            key,
            expected_val,
            POP_RESULTS_BY_LEN[n],
        ),
        {},
    )


def _setup_update_partial_overlap(n: int) -> tuple[tuple[t.Any, ...], dict[str, t.Any]]:
    return (
        (
            INT_BIDICTS_BY_LEN[n].copy(),
            PARTIAL_OVERLAP_UPDATES_BY_LEN[n],
            PARTIAL_OVERLAP_RESULTS_BY_LEN[n],
        ),
        {},
    )


def _setup_failing_update_early(n: int) -> tuple[tuple[t.Any, ...], dict[str, t.Any]]:
    return (
        (
            INT_BIDICTS_BY_LEN[n].copy(),
            INT_DICTS_BY_LEN_DUPVAL_EARLY[n],
            INT_DICTS_BY_LEN[n],
        ),
        {},
    )


def _setup_failing_update_late(n: int) -> tuple[tuple[t.Any, ...], dict[str, t.Any]]:
    return (
        (
            INT_BIDICTS_BY_LEN[n].copy(),
            INT_DICTS_BY_LEN_DUPVAL_LATE[n],
            INT_DICTS_BY_LEN[n],
        ),
        {},
    )


@pytest.mark.parametrize('kind', DATASET_NAMES)
@pytest.mark.parametrize('n', LENS)
def test_bi_init_from_dict(kind: str, n: int, benchmark: t.Any) -> None:
    """Benchmark initializing a new bidict from a dict."""
    other = DICTS_BY_KIND_AND_LEN[kind][n]
    benchmark.pedantic(bidict.bidict, args=(other,))


@pytest.mark.parametrize('n', LENS)
def test_bi_init_from_bi(n: int, benchmark: t.Any) -> None:
    """Benchmark initializing a bidict from another bidict."""
    other = INT_BIDICTS_BY_LEN[n]
    benchmark.pedantic(bidict.bidict, args=(other,))


@pytest.mark.parametrize('n', LENS)
def test_bi_init_fail_early_dupval(n: int, benchmark: t.Any) -> None:
    """Benchmark failing initialization when a duplicate value appears near the start."""
    other = INT_DICTS_BY_LEN_DUPVAL_EARLY[n]

    def failing_init() -> None:
        with pytest.raises(bidict.DuplicationError):
            bidict.bidict(other)

    benchmark.pedantic(failing_init)


@pytest.mark.parametrize('n', LENS)
def test_bi_init_fail_late_dupval(n: int, benchmark: t.Any) -> None:
    """Benchmark failing initialization when a duplicate value appears at the end."""
    other = INT_DICTS_BY_LEN_DUPVAL_LATE[n]

    def failing_init() -> None:
        with pytest.raises(bidict.DuplicationError):
            bidict.bidict(other)

    benchmark.pedantic(failing_init)


@pytest.mark.parametrize('kind', DATASET_NAMES)
@pytest.mark.parametrize('n', LENS)
def test_bi_getitem_present(kind: str, n: int, benchmark: t.Any) -> None:
    """Benchmark forward lookup of an existing key."""
    bi = BIDICTS_BY_KIND_AND_LEN[kind][n]
    key, val = LOOKUP_ITEMS_BY_KIND_AND_LEN[kind][n]
    result = benchmark.pedantic(bi.__getitem__, args=(key,))
    assert result == val


@pytest.mark.parametrize('kind', DATASET_NAMES)
@pytest.mark.parametrize('n', LENS)
def test_bi_inverse_getitem_present(kind: str, n: int, benchmark: t.Any) -> None:
    """Benchmark inverse lookup of an existing value."""
    bi = BIDICTS_BY_KIND_AND_LEN[kind][n]
    key, val = LOOKUP_ITEMS_BY_KIND_AND_LEN[kind][n]
    result = benchmark.pedantic(bi.inverse.__getitem__, args=(val,))
    assert result == key


@pytest.mark.parametrize('n', LENS)
def test_bi_setitem_new_item(n: int, benchmark: t.Any) -> None:
    """Benchmark inserting one new item into an existing bidict."""
    benchmark.pedantic(
        _setitem,
        setup=lambda n=n: _setup_setitem_new(n),
        teardown=_assert_mapping_matches,
    )


@pytest.mark.parametrize('n', LENS)
def test_bi_setitem_replace_existing_key(n: int, benchmark: t.Any) -> None:
    """Benchmark replacing the value for an existing key with a new unique value."""
    benchmark.pedantic(
        _setitem,
        setup=lambda n=n: _setup_setitem_replace_existing_key(n),
        teardown=_assert_mapping_matches,
    )


@pytest.mark.parametrize('n', LENS)
def test_bi_forceput_existing_value(n: int, benchmark: t.Any) -> None:
    """Benchmark forceput when the provided value is already associated with another key."""
    benchmark.pedantic(
        _forceput,
        setup=lambda n=n: _setup_forceput_existing_value(n),
        teardown=_assert_mapping_matches,
    )


@pytest.mark.parametrize('n', LENS)
def test_bi_pop_existing_key(n: int, benchmark: t.Any) -> None:
    """Benchmark popping an existing key."""
    result = benchmark.pedantic(
        _pop,
        setup=lambda n=n: _setup_pop(n),
        teardown=_assert_mapping_matches,
    )
    assert result == POP_ARGS_BY_LEN[n][1]


@pytest.mark.parametrize('n', LENS)
def test_bi_update_partial_overlap(n: int, benchmark: t.Any) -> None:
    """Benchmark updating from a mapping with a mix of overlapping and new items."""
    benchmark.pedantic(
        _update,
        setup=lambda n=n: _setup_update_partial_overlap(n),
        teardown=_assert_mapping_matches,
    )


@pytest.mark.parametrize('n', LENS)
def test_bi_update_fail_early_dupval(n: int, benchmark: t.Any) -> None:
    """Benchmark a bulk update that fails near the start and rolls back."""
    benchmark.pedantic(
        _failing_update,
        setup=lambda n=n: _setup_failing_update_early(n),
        teardown=_assert_mapping_matches,
    )


@pytest.mark.parametrize('n', LENS)
def test_bi_update_fail_late_dupval(n: int, benchmark: t.Any) -> None:
    """Benchmark a bulk update that fails at the end and rolls back."""
    benchmark.pedantic(
        _failing_update,
        setup=lambda n=n: _setup_failing_update_late(n),
        teardown=_assert_mapping_matches,
    )


@pytest.mark.parametrize('n', LENS)
def test_bi_iter(n: int, benchmark: t.Any) -> None:
    """Benchmark iterating over a bidict."""
    bi = INT_BIDICTS_BY_LEN[n]
    benchmark.pedantic(consume, args=(iter(bi),))


@pytest.mark.parametrize('n', LENS)
def test_orderedbi_iter(n: int, benchmark: t.Any) -> None:
    """Benchmark iterating over an OrderedBidict."""
    ob = ORDERED_BIDICTS_BY_LEN[n]
    benchmark.pedantic(consume, args=(iter(ob),))


@pytest.mark.parametrize('n', LENS)
def test_bi_equals_with_equal_dict(n: int, benchmark: t.Any) -> None:
    """Benchmark bidict.__eq__ with an equivalent dict."""
    bi, d = BIDICT_AND_DICT_LAST_TWO_ITEMS_DIFFERENT_ORDER[n]
    result = benchmark.pedantic(bi.__eq__, args=(d,))
    assert result


@pytest.mark.parametrize('n', LENS)
def test_orderedbi_items_equals_with_equal_dict_items(n: int, benchmark: t.Any) -> None:
    """Benchmark OrderedBidict.items().__eq__ with equivalent dict_items."""
    ob, d = ORDERED_BIDICT_AND_DICT_LAST_TWO_ITEMS_DIFFERENT_ORDER[n]
    result = benchmark.pedantic(ob.items().__eq__, args=(d.items(),))
    assert result


@pytest.mark.parametrize('n', LENS)
def test_copy(n: int, benchmark: t.Any) -> None:
    """Benchmark creating a copy of a bidict."""
    bi = INT_BIDICTS_BY_LEN[n]
    benchmark.pedantic(bi.copy)


@pytest.mark.parametrize('n', LENS)
def test_pickle(n: int, benchmark: t.Any) -> None:
    """Benchmark pickling a bidict."""
    bi = INT_BIDICTS_BY_LEN[n]
    benchmark.pedantic(pickle.dumps, args=(bi,))


@pytest.mark.parametrize('n', LENS)
def test_unpickle(n: int, benchmark: t.Any) -> None:
    """Benchmark unpickling a bidict."""
    bp = pickle.dumps(INT_BIDICTS_BY_LEN[n])
    benchmark.pedantic(pickle.loads, args=(bp,))

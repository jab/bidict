# Copyright 2009-2026 Joshua Bronson. All rights reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Microbenchmarks.

Uses https://pytest-benchmark.readthedocs.io/en/v4.0.0/pedantic.html,
which ../callgrind.py (as used by ../.github/workflows/benchmark.yml) requires.
"""

from __future__ import annotations

import contextlib
import pickle
import typing as t
from collections import deque
from functools import partial

import pytest

import bidict
import callgrind


consume: t.Any = partial(deque, maxlen=0)

#: Rounds per benchmark. When the benchmarks are timed, the reported figure is the min over
#: these, so that one unlucky sample cannot dominate a result. (pedantic() defaults to a single
#: round, i.e. no filtering.) ../callgrind.py counts instructions instead, which needs no such
#: filtering, so it gets one round: more would multiply its cost, and pytest-benchmark's
#: statistics over several rounds' timings would perturb the counts of the benchmarks after.
ROUNDS = 1 if callgrind.ACTIVE else 5

#: Iterations per round for an operation too cheap to measure on its own. Running this suite
#: under ../callgrind.py puts a fixed floor of roughly 11,000 instructions on each round of timed
#: calls -- some 25 times what e.g. a lookup costs -- so unless the operation is repeated within
#: the round, the result is nearly all floor and carries little signal. Only valid for operations
#: that can be repeated without fresh setup.
CHEAP_ITERATIONS = 1000

#: Roughly how many items a single round should process, for operations whose cost scales
#: with the number of items. See :func:`scaled_iterations`.
TARGET_ITEMS_PER_ROUND = 20_000


def scaled_iterations(n: int) -> int:
    """Iterations per round for an operation whose cost scales with *n*.

    Keeps the work done per round roughly constant across sizes, so that the smallest sizes
    clear the measurement floor described above without making the largest ones slow.
    """
    return max(1, TARGET_ITEMS_PER_ROUND // n)


#: Writes performed per timed call by the single-item write benchmarks below.
#:
#: Those benchmarks cannot use `iterations`: each needs a bidict in a known state, setup runs
#: once per round rather than once per iteration, and repeating a write would not exercise the
#: same path the second time. That left one write per timed call, which costs about as much as
#: the floor above, so the reported figure was largely floor. Batching this many
#: writes into a single timed call lifts them clear of it, at a fraction of what raising `rounds`
#: to the same effect would cost, since the per-round setup copies the whole bidict.
#:
#: They therefore measure the cost of a run of writes rather than of one in isolation. For the
#: smaller sizes the batch consumes most of the contained items, so the bidict grows or shrinks
#: appreciably during it -- which is representative, and identical across the revisions being
#: compared, so it does not affect what the comparison means.
WRITES_PER_ROUND = 1_000


def scaled_writes(n: int) -> int:
    """How many writes the single-item write benchmarks perform per timed call, for size *n*.

    Capped by *n*, since some of them consume a distinct contained item per write.
    """
    return min(n, WRITES_PER_ROUND)


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

# One batch of items per single-item write benchmark, sized by scaled_writes(). Every item in
# a batch takes the same path through the code as the others, so the batch measures that path.

#: New keys and new values: no duplication.
SETITEM_NEW_ITEMS_BY_LEN: dict[int, list[tuple[int, int]]] = {
    n: [(-i, -i) for i in range(1, scaled_writes(n) + 1)] for n in LENS
}
SETITEM_NEW_RESULTS_BY_LEN: dict[int, dict[int, int]] = {
    n: INT_DICTS_BY_LEN[n] | dict(SETITEM_NEW_ITEMS_BY_LEN[n]) for n in LENS
}

#: Contained keys paired with new values: key duplication.
SETITEM_REPLACE_ITEMS_BY_LEN: dict[int, list[tuple[int, int]]] = {
    n: [(n - i, -i) for i in range(1, scaled_writes(n) + 1)] for n in LENS
}
SETITEM_REPLACE_RESULTS_BY_LEN: dict[int, dict[int, int]] = {
    n: INT_DICTS_BY_LEN[n] | dict(SETITEM_REPLACE_ITEMS_BY_LEN[n]) for n in LENS
}

#: New keys paired with contained values: value duplication, collapsing an item each time.
FORCEPUT_ITEMS_BY_LEN: dict[int, list[tuple[int, int]]] = {
    n: [(-i, i - 1) for i in range(1, scaled_writes(n) + 1)] for n in LENS
}
FORCEPUT_RESULTS_BY_LEN: dict[int, dict[int, int]] = {
    n: {k: v for k, v in INT_DICTS_BY_LEN[n].items() if k >= scaled_writes(n)} | dict(FORCEPUT_ITEMS_BY_LEN[n])
    for n in LENS
}

POP_KEYS_BY_LEN: dict[int, list[int]] = {n: [n - i for i in range(1, scaled_writes(n) + 1)] for n in LENS}
POP_RESULTS_BY_LEN: dict[int, dict[int, int]] = {
    n: {k: v for k, v in INT_DICTS_BY_LEN[n].items() if k not in set(POP_KEYS_BY_LEN[n])} for n in LENS
}

#: The first keys, whose items move_to_end() moves from the front of an OrderedBidict to the end.
MOVE_KEYS_BY_LEN: dict[int, list[int]] = {n: list(range(scaled_writes(n))) for n in LENS}

PARTIAL_OVERLAP_UPDATES_BY_LEN: dict[int, dict[int, int]] = {
    n: {i: i for i in range(n // 2, n + (n // 2))} for n in LENS
}
PARTIAL_OVERLAP_RESULTS_BY_LEN: dict[int, dict[int, int]] = {
    n: (INT_DICTS_BY_LEN[n] | PARTIAL_OVERLAP_UPDATES_BY_LEN[n]) for n in LENS
}

#: New items, one more than the bidict contains.
LARGER_UPDATES_BY_LEN: dict[int, dict[int, int]] = {n: {-i: -i for i in range(1, n + 2)} for n in LENS}
LARGER_UPDATE_RESULTS_BY_LEN: dict[int, dict[int, int]] = {
    n: INT_DICTS_BY_LEN[n] | LARGER_UPDATES_BY_LEN[n] for n in LENS
}

# Failing updates. Every item before the failing one is new, so it gets written and must then
# be rolled back. (Unlike INT_DICTS_BY_LEN_DUPVAL_*, whose items before the failing one are all
# already contained, and so would not be written.) The failing item's value is already contained.

#: Writes one item, then fails.
FAILING_UPDATES_EARLY_BY_LEN: dict[int, dict[int, int]] = {
    n: dict([(-1, -1), (-2, 0), *((-i, -i) for i in range(3, n + 1))]) for n in LENS
}
#: Writes all but the last item, then fails.
FAILING_UPDATES_LATE_BY_LEN: dict[int, dict[int, int]] = {n: {-i: -i for i in range(1, n)} | {-n: 0} for n in LENS}

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


def _setitem(bi: bidict.MutableBidict[int, int], items: list[tuple[int, int]], _expected: dict[int, int]) -> None:
    for key, val in items:
        bi[key] = val


def _forceput(bi: bidict.bidict[int, int], items: list[tuple[int, int]], _expected: dict[int, int]) -> None:
    for key, val in items:
        bi.forceput(key, val)


def _update(bi: bidict.bidict[int, int], other: dict[int, int], _expected: dict[int, int]) -> None:
    bi.update(other)


def _failing_update(bi: bidict.bidict[int, int], other: dict[int, int], _expected: dict[int, int]) -> None:
    with pytest.raises(bidict.DuplicationError):
        bi.update(other)


def _pop(bi: bidict.MutableBidict[int, int], keys: list[int], _expected: dict[int, int]) -> None:
    for key in keys:
        bi.pop(key)


def _del(bi: bidict.bidict[int, int], keys: list[int], _expected: dict[int, int]) -> None:
    for key in keys:
        del bi[key]


def _popitem(bi: bidict.MutableBidict[int, int], count: int, _expected: dict[int, int]) -> None:
    for _ in range(count):
        bi.popitem()


def _move_to_end(ob: bidict.OrderedBidict[int, int], keys: list[int], _expected: dict[int, int]) -> None:
    for key in keys:
        ob.move_to_end(key)


def _assert_mapping_matches(*args: t.Any) -> None:
    assert dict(args[0]) == args[-1]


def _setup_setitem_new(n: int) -> tuple[tuple[t.Any, ...], dict[str, t.Any]]:
    return ((INT_BIDICTS_BY_LEN[n].copy(), SETITEM_NEW_ITEMS_BY_LEN[n], SETITEM_NEW_RESULTS_BY_LEN[n]), {})


def _setup_setitem_replace_existing_key(n: int) -> tuple[tuple[t.Any, ...], dict[str, t.Any]]:
    return ((INT_BIDICTS_BY_LEN[n].copy(), SETITEM_REPLACE_ITEMS_BY_LEN[n], SETITEM_REPLACE_RESULTS_BY_LEN[n]), {})


def _setup_forceput_existing_value(n: int) -> tuple[tuple[t.Any, ...], dict[str, t.Any]]:
    return ((INT_BIDICTS_BY_LEN[n].copy(), FORCEPUT_ITEMS_BY_LEN[n], FORCEPUT_RESULTS_BY_LEN[n]), {})


def _setup_pop(n: int) -> tuple[tuple[t.Any, ...], dict[str, t.Any]]:
    return ((INT_BIDICTS_BY_LEN[n].copy(), POP_KEYS_BY_LEN[n], POP_RESULTS_BY_LEN[n]), {})


def _setup_popitem(n: int) -> tuple[tuple[t.Any, ...], dict[str, t.Any]]:
    # popitem() removes the last item added, so it removes the same keys as POP_KEYS_BY_LEN[n].
    return ((INT_BIDICTS_BY_LEN[n].copy(), len(POP_KEYS_BY_LEN[n]), POP_RESULTS_BY_LEN[n]), {})


# Each int in INT_DICTS_BY_LEN[n] maps to itself, so its inverse has the same keys, and the same results.
def _setup_inverse_pop(n: int) -> tuple[tuple[t.Any, ...], dict[str, t.Any]]:
    return ((INT_BIDICTS_BY_LEN[n].copy().inverse, POP_KEYS_BY_LEN[n], POP_RESULTS_BY_LEN[n]), {})


def _setup_inverse_popitem(n: int) -> tuple[tuple[t.Any, ...], dict[str, t.Any]]:
    return ((INT_BIDICTS_BY_LEN[n].copy().inverse, len(POP_KEYS_BY_LEN[n]), POP_RESULTS_BY_LEN[n]), {})


def _setup_orderedbi_setitem_replace_existing_key(n: int) -> tuple[tuple[t.Any, ...], dict[str, t.Any]]:
    return ((ORDERED_BIDICTS_BY_LEN[n].copy(), SETITEM_REPLACE_ITEMS_BY_LEN[n], SETITEM_REPLACE_RESULTS_BY_LEN[n]), {})


def _setup_orderedbi_pop(n: int) -> tuple[tuple[t.Any, ...], dict[str, t.Any]]:
    return ((ORDERED_BIDICTS_BY_LEN[n].copy(), POP_KEYS_BY_LEN[n], POP_RESULTS_BY_LEN[n]), {})


def _setup_orderedbi_popitem(n: int) -> tuple[tuple[t.Any, ...], dict[str, t.Any]]:
    return ((ORDERED_BIDICTS_BY_LEN[n].copy(), len(POP_KEYS_BY_LEN[n]), POP_RESULTS_BY_LEN[n]), {})


def _setup_orderedbi_move_to_end(n: int) -> tuple[tuple[t.Any, ...], dict[str, t.Any]]:
    return ((ORDERED_BIDICTS_BY_LEN[n].copy(), MOVE_KEYS_BY_LEN[n], INT_DICTS_BY_LEN[n]), {})


def _setup_update_partial_overlap(n: int) -> tuple[tuple[t.Any, ...], dict[str, t.Any]]:
    return (
        (
            INT_BIDICTS_BY_LEN[n].copy(),
            PARTIAL_OVERLAP_UPDATES_BY_LEN[n],
            PARTIAL_OVERLAP_RESULTS_BY_LEN[n],
        ),
        {},
    )


def _setup_update_larger(n: int) -> tuple[tuple[t.Any, ...], dict[str, t.Any]]:
    return ((INT_BIDICTS_BY_LEN[n].copy(), LARGER_UPDATES_BY_LEN[n], LARGER_UPDATE_RESULTS_BY_LEN[n]), {})


def _setup_failing_update_early(n: int) -> tuple[tuple[t.Any, ...], dict[str, t.Any]]:
    return (
        (
            INT_BIDICTS_BY_LEN[n].copy(),
            FAILING_UPDATES_EARLY_BY_LEN[n],
            INT_DICTS_BY_LEN[n],
        ),
        {},
    )


def _setup_failing_update_late(n: int) -> tuple[tuple[t.Any, ...], dict[str, t.Any]]:
    return (
        (
            INT_BIDICTS_BY_LEN[n].copy(),
            FAILING_UPDATES_LATE_BY_LEN[n],
            INT_DICTS_BY_LEN[n],
        ),
        {},
    )


@pytest.mark.parametrize('kind', DATASET_NAMES)
@pytest.mark.parametrize('n', LENS)
def test_bi_init_from_dict(kind: str, n: int, benchmark: t.Any) -> None:
    """Benchmark initializing a new bidict from a dict."""
    other = DICTS_BY_KIND_AND_LEN[kind][n]
    benchmark.pedantic(bidict.bidict, args=(other,), rounds=ROUNDS, iterations=scaled_iterations(n))


@pytest.mark.parametrize('n', LENS)
def test_bi_init_from_bi(n: int, benchmark: t.Any) -> None:
    """Benchmark initializing a bidict from another bidict."""
    other = INT_BIDICTS_BY_LEN[n]
    benchmark.pedantic(bidict.bidict, args=(other,), rounds=ROUNDS, iterations=scaled_iterations(n))


@pytest.mark.parametrize('n', LENS)
def test_bi_init_fail_early_dupval(n: int, benchmark: t.Any) -> None:
    """Benchmark failing initialization when a duplicate value appears near the start."""
    other = INT_DICTS_BY_LEN_DUPVAL_EARLY[n]

    def failing_init() -> None:
        with pytest.raises(bidict.DuplicationError):
            bidict.bidict(other)

    benchmark.pedantic(failing_init, rounds=ROUNDS, iterations=scaled_iterations(n))


@pytest.mark.parametrize('n', LENS)
def test_bi_init_fail_late_dupval(n: int, benchmark: t.Any) -> None:
    """Benchmark failing initialization when a duplicate value appears at the end."""
    other = INT_DICTS_BY_LEN_DUPVAL_LATE[n]

    def failing_init() -> None:
        with pytest.raises(bidict.DuplicationError):
            bidict.bidict(other)

    benchmark.pedantic(failing_init, rounds=ROUNDS, iterations=scaled_iterations(n))


@pytest.mark.parametrize('kind', DATASET_NAMES)
@pytest.mark.parametrize('n', LENS)
def test_bi_getitem_present(kind: str, n: int, benchmark: t.Any) -> None:
    """Benchmark forward lookup of an existing key."""
    bi = BIDICTS_BY_KIND_AND_LEN[kind][n]
    key, val = LOOKUP_ITEMS_BY_KIND_AND_LEN[kind][n]
    result = benchmark.pedantic(bi.__getitem__, args=(key,), rounds=ROUNDS, iterations=CHEAP_ITERATIONS)
    assert result == val


@pytest.mark.parametrize('kind', DATASET_NAMES)
@pytest.mark.parametrize('n', LENS)
def test_bi_inverse_getitem_present(kind: str, n: int, benchmark: t.Any) -> None:
    """Benchmark inverse lookup of an existing value."""
    bi = BIDICTS_BY_KIND_AND_LEN[kind][n]
    key, val = LOOKUP_ITEMS_BY_KIND_AND_LEN[kind][n]
    result = benchmark.pedantic(bi.inverse.__getitem__, args=(val,), rounds=ROUNDS, iterations=CHEAP_ITERATIONS)
    assert result == key


@pytest.mark.parametrize('n', LENS)
def test_bi_setitem_new_item(n: int, benchmark: t.Any) -> None:
    """Benchmark inserting new items into an existing bidict."""
    benchmark.pedantic(
        _setitem,
        setup=lambda n=n: _setup_setitem_new(n),
        teardown=_assert_mapping_matches,
        rounds=ROUNDS,
    )


@pytest.mark.parametrize('n', LENS)
def test_bi_setitem_replace_existing_key(n: int, benchmark: t.Any) -> None:
    """Benchmark replacing the values of existing keys with new unique values."""
    benchmark.pedantic(
        _setitem,
        setup=lambda n=n: _setup_setitem_replace_existing_key(n),
        teardown=_assert_mapping_matches,
        rounds=ROUNDS,
    )


@pytest.mark.parametrize('n', LENS)
def test_bi_forceput_existing_value(n: int, benchmark: t.Any) -> None:
    """Benchmark forceput when each provided value is already associated with another key."""
    benchmark.pedantic(
        _forceput,
        setup=lambda n=n: _setup_forceput_existing_value(n),
        teardown=_assert_mapping_matches,
        rounds=ROUNDS,
    )


@pytest.mark.parametrize('n', LENS)
def test_bi_pop_existing_key(n: int, benchmark: t.Any) -> None:
    """Benchmark popping existing keys."""
    benchmark.pedantic(
        _pop,
        setup=lambda n=n: _setup_pop(n),
        teardown=_assert_mapping_matches,
        rounds=ROUNDS,
    )


@pytest.mark.parametrize('n', LENS)
def test_bi_del_existing_key(n: int, benchmark: t.Any) -> None:
    """Benchmark deleting existing keys."""
    benchmark.pedantic(
        _del,
        setup=lambda n=n: _setup_pop(n),
        teardown=_assert_mapping_matches,
        rounds=ROUNDS,
    )


@pytest.mark.parametrize('n', LENS)
def test_bi_popitem(n: int, benchmark: t.Any) -> None:
    """Benchmark popping items."""
    benchmark.pedantic(
        _popitem,
        setup=lambda n=n: _setup_popitem(n),
        teardown=_assert_mapping_matches,
        rounds=ROUNDS,
    )


@pytest.mark.parametrize('n', LENS)
def test_bi_inverse_pop_existing_key(n: int, benchmark: t.Any) -> None:
    """Benchmark popping existing keys through the inverse."""
    benchmark.pedantic(
        _pop,
        setup=lambda n=n: _setup_inverse_pop(n),
        teardown=_assert_mapping_matches,
        rounds=ROUNDS,
    )


@pytest.mark.parametrize('n', LENS)
def test_bi_inverse_popitem(n: int, benchmark: t.Any) -> None:
    """Benchmark popping items through the inverse."""
    benchmark.pedantic(
        _popitem,
        setup=lambda n=n: _setup_inverse_popitem(n),
        teardown=_assert_mapping_matches,
        rounds=ROUNDS,
    )


@pytest.mark.parametrize('n', LENS)
def test_orderedbi_setitem_replace_existing_key(n: int, benchmark: t.Any) -> None:
    """Benchmark replacing the values of an OrderedBidict's existing keys with new unique values."""
    benchmark.pedantic(
        _setitem,
        setup=lambda n=n: _setup_orderedbi_setitem_replace_existing_key(n),
        teardown=_assert_mapping_matches,
        rounds=ROUNDS,
    )


@pytest.mark.parametrize('n', LENS)
def test_orderedbi_pop_existing_key(n: int, benchmark: t.Any) -> None:
    """Benchmark popping an OrderedBidict's existing keys."""
    benchmark.pedantic(
        _pop,
        setup=lambda n=n: _setup_orderedbi_pop(n),
        teardown=_assert_mapping_matches,
        rounds=ROUNDS,
    )


@pytest.mark.parametrize('n', LENS)
def test_orderedbi_popitem(n: int, benchmark: t.Any) -> None:
    """Benchmark popping an OrderedBidict's items."""
    benchmark.pedantic(
        _popitem,
        setup=lambda n=n: _setup_orderedbi_popitem(n),
        teardown=_assert_mapping_matches,
        rounds=ROUNDS,
    )


@pytest.mark.parametrize('n', LENS)
def test_orderedbi_move_to_end(n: int, benchmark: t.Any) -> None:
    """Benchmark moving an OrderedBidict's first items to the end."""
    benchmark.pedantic(
        _move_to_end,
        setup=lambda n=n: _setup_orderedbi_move_to_end(n),
        teardown=_assert_mapping_matches,
        rounds=ROUNDS,
    )


@pytest.mark.parametrize('n', LENS)
def test_bi_update_partial_overlap(n: int, benchmark: t.Any) -> None:
    """Benchmark updating from a mapping with a mix of overlapping and new items."""
    benchmark.pedantic(
        _update,
        setup=lambda n=n: _setup_update_partial_overlap(n),
        teardown=_assert_mapping_matches,
        rounds=ROUNDS,
    )


@pytest.mark.parametrize('n', LENS)
def test_bi_update_larger(n: int, benchmark: t.Any) -> None:
    """Benchmark updating from a mapping of more new items than the bidict contains."""
    benchmark.pedantic(
        _update,
        setup=lambda n=n: _setup_update_larger(n),
        teardown=_assert_mapping_matches,
        rounds=ROUNDS,
    )


@pytest.mark.parametrize('n', LENS)
def test_bi_update_fail_early_dupval(n: int, benchmark: t.Any) -> None:
    """Benchmark a bulk update that fails near the start and rolls back."""
    benchmark.pedantic(
        _failing_update,
        setup=lambda n=n: _setup_failing_update_early(n),
        teardown=_assert_mapping_matches,
        rounds=ROUNDS,
    )


@pytest.mark.parametrize('n', LENS)
def test_bi_update_fail_late_dupval(n: int, benchmark: t.Any) -> None:
    """Benchmark a bulk update that fails at the end and rolls back."""
    benchmark.pedantic(
        _failing_update,
        setup=lambda n=n: _setup_failing_update_late(n),
        teardown=_assert_mapping_matches,
        rounds=ROUNDS,
    )


@pytest.mark.parametrize(
    'setup',
    [
        _setup_update_partial_overlap,
        _setup_update_larger,
        _setup_failing_update_early,
        _setup_failing_update_late,
    ],
)
@pytest.mark.parametrize('n', LENS)
def test_update_workloads_take_intended_path(setup: t.Any, n: int, monkeypatch: t.Any) -> None:
    """Not a benchmark: check that each update benchmark above exercises the path it is meant to.

    Its data alone doesn't show this: items already contained are never written, so a failing
    update made only of those has nothing to roll back. Each must write items in place,
    recording the unwrites that would roll it back.
    """
    (bi, other, _expected), _ = setup(n)
    unwrites_per_write: list[t.Any] = []
    write = bidict.BidictBase._write

    def spy(self: t.Any, *args: t.Any, unwrites: t.Any) -> None:
        unwrites_per_write.append(unwrites)
        write(self, *args, unwrites=unwrites)

    monkeypatch.setattr(bidict.BidictBase, '_write', spy)
    with contextlib.suppress(bidict.DuplicationError):
        bi.update(other)
    assert unwrites_per_write
    assert all(unwrites is not None for unwrites in unwrites_per_write)


@pytest.mark.parametrize('n', LENS)
def test_bi_iter(n: int, benchmark: t.Any) -> None:
    """Benchmark iterating over a bidict."""
    bi = INT_BIDICTS_BY_LEN[n]
    # Build the iterator inside the timed callable: one pre-built and passed via args
    # would already be exhausted by the second of the repeated calls below.
    benchmark.pedantic(lambda: consume(iter(bi)), rounds=ROUNDS, iterations=scaled_iterations(n))


@pytest.mark.parametrize('n', LENS)
def test_orderedbi_iter(n: int, benchmark: t.Any) -> None:
    """Benchmark iterating over an OrderedBidict."""
    ob = ORDERED_BIDICTS_BY_LEN[n]
    # Build the iterator inside the timed callable: one pre-built and passed via args
    # would already be exhausted by the second of the repeated calls below.
    benchmark.pedantic(lambda: consume(iter(ob)), rounds=ROUNDS, iterations=scaled_iterations(n))


@pytest.mark.parametrize('n', LENS)
def test_bi_equals_with_equal_dict(n: int, benchmark: t.Any) -> None:
    """Benchmark bidict.__eq__ with an equivalent dict."""
    bi, d = BIDICT_AND_DICT_LAST_TWO_ITEMS_DIFFERENT_ORDER[n]
    result = benchmark.pedantic(bi.__eq__, args=(d,), rounds=ROUNDS, iterations=scaled_iterations(n))
    assert result


@pytest.mark.parametrize('n', LENS)
def test_orderedbi_items_equals_with_equal_dict_items(n: int, benchmark: t.Any) -> None:
    """Benchmark OrderedBidict.items().__eq__ with equivalent dict_items."""
    ob, d = ORDERED_BIDICT_AND_DICT_LAST_TWO_ITEMS_DIFFERENT_ORDER[n]
    result = benchmark.pedantic(ob.items().__eq__, args=(d.items(),), rounds=ROUNDS, iterations=scaled_iterations(n))
    assert result


@pytest.mark.parametrize('n', LENS)
def test_copy(n: int, benchmark: t.Any) -> None:
    """Benchmark creating a copy of a bidict."""
    bi = INT_BIDICTS_BY_LEN[n]
    benchmark.pedantic(bi.copy, rounds=ROUNDS, iterations=scaled_iterations(n))


@pytest.mark.parametrize('n', LENS)
def test_pickle(n: int, benchmark: t.Any) -> None:
    """Benchmark pickling a bidict."""
    bi = INT_BIDICTS_BY_LEN[n]
    benchmark.pedantic(pickle.dumps, args=(bi,), rounds=ROUNDS, iterations=scaled_iterations(n))


@pytest.mark.parametrize('n', LENS)
def test_unpickle(n: int, benchmark: t.Any) -> None:
    """Benchmark unpickling a bidict."""
    bp = pickle.dumps(INT_BIDICTS_BY_LEN[n])
    benchmark.pedantic(pickle.loads, args=(bp,), rounds=ROUNDS, iterations=scaled_iterations(n))

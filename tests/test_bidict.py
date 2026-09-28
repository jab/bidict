# Copyright 2009-2026 Joshua Bronson. All rights reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Tests for :mod:`bidict`.

Mainly these are property-based tests implemented via https://hypothesis.works.
"""

from __future__ import annotations

import gc
import operator
import pickle
import sys
import typing as t
import weakref
from collections import UserDict
from collections.abc import Callable
from collections.abc import Iterator
from collections.abc import KeysView
from collections.abc import Mapping
from collections.abc import Reversible
from collections.abc import Sequence
from copy import copy
from copy import deepcopy
from functools import partial
from functools import reduce
from itertools import count
from itertools import product
from itertools import starmap
from random import Random
from typing import assert_type
from unittest.mock import ANY

import pytest
from bidict_test_fixtures import BAD_ITEMS
from bidict_test_fixtures import BB
from bidict_test_fixtures import BT
from bidict_test_fixtures import KT
from bidict_test_fixtures import MBT
from bidict_test_fixtures import SET_OPS
from bidict_test_fixtures import VT
from bidict_test_fixtures import AsymLookup
from bidict_test_fixtures import AsymStored
from bidict_test_fixtures import CaseFoldingDict
from bidict_test_fixtures import Handle
from bidict_test_fixtures import HashFailed
from bidict_test_fixtures import HashFails
from bidict_test_fixtures import KeysViaGetattr
from bidict_test_fixtures import LegacySequence
from bidict_test_fixtures import Oracle
from bidict_test_fixtures import SupportsKeysAndGetItem
from bidict_test_fixtures import Tagged
from bidict_test_fixtures import UserBi
from bidict_test_fixtures import UserBiBackedByDictSub
from bidict_test_fixtures import UserBiBackedByReversibleNonDict
from bidict_test_fixtures import UserBiBackedByReversibleValues
from bidict_test_fixtures import UserBiBackedBySortedDict
from bidict_test_fixtures import UserBiNotOwnInv
from bidict_test_fixtures import UserOrderedBi
from bidict_test_fixtures import UserOrderedBiBackedBySortedDict
from bidict_test_fixtures import UserOrderedBiBase
from bidict_test_fixtures import WriteRefused
from bidict_test_fixtures import bidict_refusing_nth_write
from bidict_test_fixtures import bidict_types
from bidict_test_fixtures import bomb
from bidict_test_fixtures import dedup
from bidict_test_fixtures import invdict
from bidict_test_fixtures import mutable_bidict_types
from bidict_test_fixtures import pickle_copy
from bidict_test_fixtures import powerset
from bidict_test_fixtures import should_be_reversible
from bidict_test_fixtures import update_arg_types
from bidict_test_fixtures import zip_equal
from hypothesis import assume
from hypothesis import example
from hypothesis import given
from hypothesis import note
from hypothesis.stateful import RuleBasedStateMachine
from hypothesis.stateful import initialize
from hypothesis.stateful import invariant
from hypothesis.stateful import precondition
from hypothesis.stateful import rule
from hypothesis.strategies import booleans
from hypothesis.strategies import randoms
from hypothesis.strategies import sampled_from
from typing_extensions import TypeIs

from bidict import ON_DUP_DROP_OLD
from bidict import BidictKeysView
from bidict import BidirectionalMapping
from bidict import DuplicationError
from bidict import KeyAndValueDuplicationError
from bidict import MutableBidict
from bidict import MutableBidirectionalMapping
from bidict import OnDup
from bidict import OnDupAction
from bidict import OrderedBidict
from bidict import OrderedBidictBase
from bidict import ValueDuplicationError
from bidict import bidict
from bidict import frozenbidict
from bidict import inverted
from bidict._orderedbase import Node as OrderedBidictNode
from bidict._orderedbase import WeakAttr
from bidict._typing import MapOrItems
from bidict._typing import override


Items = Sequence[tuple[int, int]]
Items121 = dict[t.Any, t.Any]

ks = tuple(range(1, 5))
vs = tuple(range(-1, -5, -1))
keys = sampled_from(ks)
vals = sampled_from(vs)
items = sampled_from(list(powerset(product(ks, vs))))
items121 = items.map(dedup)
# Items that can never duplicate anything in a bidict under test: their keys and values are
# disjoint from ks and vs, and they are 1:1 among themselves.
fresh_items = sampled_from(list(powerset((k, -k) for k in range(5, 9))))
bidict_t = sampled_from(bidict_types)
mut_bidict_t = sampled_from(mutable_bidict_types)
updates_t = sampled_from(update_arg_types)
on_dups = tuple(starmap(OnDup, product(OnDupAction, repeat=2)))
on_dup = sampled_from(on_dups)


def is_ordered(bi: BidirectionalMapping[int, int]) -> TypeIs[OrderedBidict[int, int]]:
    return isinstance(bi, OrderedBidict)


class BidictStateMachine(RuleBasedStateMachine):
    bi: MutableBidict[int, int]
    oracle: Oracle[int, int]

    @initialize(mut_bidict_t=mut_bidict_t, items121=items121)
    def init(self, mut_bidict_t: type[MutableBidict[int, int]], items121: Items121) -> None:
        self.bi = mut_bidict_t(items121)
        self.oracle = Oracle(items121, ordered=self.is_ordered())

    def is_ordered(self) -> bool:
        return is_ordered(self.bi)

    @invariant()
    def assert_match_oracle(self) -> None:
        note(f'> {self.bi=}\n> {self.oracle.data=}')
        self.oracle.assert_match(self.bi)

    viewnames = sampled_from(('keys', 'values', 'items'))

    # TODO: Try @invariant rather than @rule now that hypothesis is faster / it might not slow down the tests too much.
    @rule(rand=randoms(), viewname=viewnames, set_op=sampled_from(SET_OPS), other_set=items.map(frozenset))
    def assert_views_match_oracle(self, rand: Random, viewname: str, set_op: t.Any, other_set: t.Any) -> None:
        check = getattr(self.bi, viewname)()
        expect = getattr(self.oracle.data, viewname)() if viewname != 'values' else self.oracle.data_inv.keys()
        assert len(check) == len(expect)
        if self.is_ordered():
            assert zip_equal(check, expect)
        else:
            assert check == frozenset(expect)
        missing = ('foo', 'bar') if viewname == 'items' else 'foo'
        assert missing not in check
        if self.oracle.data:
            contained = rand.choice(tuple(expect))
            assert contained in check
        if viewname != 'items':
            other_set = {k for (k, _) in other_set}
        assert_calls_match(
            partial(set_op, check, other_set),
            partial(set_op, expect, other_set),
        )
        if viewname == 'items':
            other_set = self.bi.__class__(dedup(other_set)).items()
            assert_calls_match(
                partial(set_op, check, other_set),
                partial(set_op, expect, other_set),
            )

    @invariant()
    def assert_bi_and_inv_are_inverse(self) -> None:
        assert_bi_and_inv_are_inverse(self.bi)

    @invariant()
    def assert_values_correspond_to_keys(self) -> None:
        """values() must correspond elementwise to keys(), as a plain dict's does.

        Overwriting an item reorders a non-ordered bidict's backing _invm relative to its
        _fwdm, so a values() view sourced from _invm's keys would silently mispair here.
        Only reachable by mutating: a bulk __init__ that would cause it raises instead.
        """
        for b in (self.bi, self.bi.inv):
            assert list(b.values()) == [b[k] for k in b]

    @precondition(lambda self: should_be_reversible(self.bi.__class__))
    @invariant()
    def assert_reversed_works(self) -> None:
        assert list(reversed(self.bi)) == list(self.bi)[::-1]
        items = self.bi.items()
        assert isinstance(items, Reversible)
        assert list(reversed(items)) == list(items)[::-1]
        if self.is_ordered():
            assert zip_equal(reversed(self.bi), reversed(self.oracle.data))
            assert zip_equal(reversed(items), reversed(self.oracle.data.items()))
            values = self.bi.values()
            assert isinstance(values, Reversible)
            assert zip_equal(reversed(values), reversed(self.oracle.data.values()))

    @precondition(is_ordered)
    @invariant()
    def assert_nodes_consistent(self) -> None:
        assert is_ordered(self.bi)
        for b in (self.bi, self.bi.inv):
            assert_orderedbidict_nodes_consistent(b)

    @rule()
    def copy(self) -> None:
        for cp in (copy(self.bi), deepcopy(self.bi)):
            assert_bi_and_inv_are_inverse(cp)
            assert_bidicts_equal(cp, self.bi)

    @rule()
    def pickle(self) -> None:
        for b in (self.bi, self.bi.inv):
            roundtripped = pickle_copy(b)
            assert_bi_and_inv_are_inverse(roundtripped)
            assert_bidicts_equal(roundtripped, b)

    @rule()
    def clear(self) -> None:
        self.bi.clear()
        self.oracle.clear()

    @rule(key=keys, val=vals, on_dup=on_dup)
    def put(self, key: int, val: int, on_dup: OnDup) -> None:
        assert_calls_match(
            partial(self.bi.put, key, val, on_dup),
            partial(self.oracle.put, key, val, on_dup),
        )

    @rule(updates=items, updates_t=updates_t, on_dup=on_dup)
    def putall(self, updates: MapOrItems[int, int], updates_t: t.Any, on_dup: OnDup) -> None:
        # Don't let the updates_t(updates) calls below raise a DuplicationError.
        if isinstance(updates_t, type) and issubclass(updates_t, BidirectionalMapping):
            updates = dedup(updates)
        # Since updates_t can be iter, can't extract the two updates_t(updates) calls below into a single value.
        assert_calls_match(
            partial(self.bi.putall, updates_t(updates), on_dup),
            partial(self.oracle.putall, updates_t(updates), on_dup),
        )

    @rule(new=fresh_items, on_dup=on_dup)
    def putall_with_bad_item(self, new: Items, on_dup: OnDup) -> None:
        """A bulk update whose last item raises must apply none of it, whatever the on_dup.

        The preceding items are fresh, so the only thing that can fail is the bad item.
        Pass an iterator so this always takes the incremental rollback path.
        """
        assert_update_fails_clean(self.bi, iter([*new, (bomb, 0)]), HashFailed, on_dup)

    @precondition(is_ordered)
    @rule(updates=items, on_dup=on_dup)
    def putall_with_bad_item_after_overwrites(self, updates: Items, on_dup: OnDup) -> None:
        """An ordered bidict must restore its *order* too, not just its contents.

        Unlike the rule above this lets the preceding items overwrite existing ones, which
        is what makes the linked list's order diverge from the backing mappings'. Only
        ordered bidicts guarantee this: rolling back an overwrite reinserts the overwritten
        item at the end of a backing mapping rather than in its original position, so a
        non-ordered bidict is restored contents-only. See "Updates Fail Clean" in the docs.
        """
        arg = iter([*updates, (bomb, 0)])
        assert_update_fails_clean(self.bi, arg, (HashFailed, DuplicationError), on_dup)

    @rule(on_dup=on_dup)
    def putall_own_inverse(self, on_dup: OnDup) -> None:
        """Updating from our own inverse must behave like updating from a snapshot of it, as b | b.inv does.

        The inverse shares our backing mappings, so this must not iterate over them while writing to them.
        """
        snapshot = list(self.bi.inv.items())
        assert_calls_match(
            partial(self.bi.putall, self.bi.inv, on_dup),
            partial(self.oracle.putall, snapshot, on_dup),
        )

    @rule(other=items121)
    def __ior__(self, other: Mapping[int, int]) -> None:
        assert_calls_match(
            partial(self.bi.__ior__, other),
            partial(self.oracle.__ior__, other),
        )

    @rule(other=items121)
    def __or__(self, other: Mapping[int, int]) -> None:
        assert_calls_match(
            partial(self.bi.__or__, other),
            partial(self.oracle.__or__, other),
        )

    # https://bidict.rtfd.io/basic-usage.html#order-matters
    @precondition(lambda self: zip_equal(self.bi, self.oracle.data))
    @rule(other=items121)
    def __ror__(self, other: Mapping[int, int]) -> None:
        assert_calls_match(
            partial(self.bi.__ror__, other),
            partial(self.oracle.__ror__, other),
        )

    @precondition(lambda self: len(self.bi) >= 2)
    @rule(random=randoms())
    def update_with_dup(self, random: Random) -> None:
        # Covered nondeterministically by the more general "putall" rule above, but this ensures that basic duplication
        # scenarios are deterministically covered.
        # Choose two existing items at random.
        (k1, v1), (k2, v2) = random.sample(tuple(self.oracle.data.items()), 2)
        # Inserting (new_key, dup_val) should raise ValueDuplicationError.
        assert_update_fails_clean(self.bi, [('foo', 'foo'), ('bar', v1)], ValueDuplicationError)
        # key and value duplication across two different items should raise KeyAndValueDuplicationError.
        for key, val in ((k1, v2), (k2, v1)):
            assert_update_fails_clean(self.bi, [('foo', 'foo'), (key, val)], KeyAndValueDuplicationError)
        # Inserting already-present items should be a no-op.
        before = self.bi.copy()
        self.bi.update([(k1, v1), (k2, v2)])
        assert self.bi.equals_order_sensitive(before)
        assert self.bi.inv.equals_order_sensitive(before.inv)

    def is_empty(self) -> bool:
        return not self.bi

    @precondition(is_empty)
    @rule()
    def popitem_empty(self) -> None:
        with pytest.raises(KeyError):
            self.bi.popitem()

    def is_nonempty(self) -> bool:
        return bool(self.bi)

    @precondition(is_nonempty)
    @rule(last=booleans(), flip=booleans(), inv=booleans())
    def popitem(self, last: bool, inv: bool, flip: bool) -> None:
        bi, oracle = self.bi, self.oracle
        if is_ordered(bi):
            if not inv:
                expect = oracle.popitem(last=last)
                check = bi.popitem(last=last)
            else:
                expect = oracle.popitem(last=last)[::-1]
                check = bi.inv.popitem(last=last)
            assert check == expect
            # When inv is true, check is an item of bi.inv, and it may still be in bi itself, e.g. {1: 2, 2: 1}.
            assert check not in (bi.inv if inv else bi).items()
        else:
            fst, snd = (bi, oracle) if flip else (oracle, bi)
            k, v = fst.popitem()
            assert snd.pop(k) == v
            assert (k, v) not in bi.items()

    @precondition(is_nonempty)
    @rule(random=randoms())
    def pop_randkey(self, random: Random) -> None:
        key = random.choice(tuple(self.oracle.data))
        expect = self.oracle.pop(key)
        check = self.bi.pop(key)
        assert check == expect

    @precondition(is_ordered)
    @precondition(is_nonempty)
    @rule(random=randoms(), last=booleans())
    def move_to_end_randkey(self, random: Random, last: bool) -> None:
        assert is_ordered(self.bi)
        key, val = random.choice(tuple(self.oracle.data.items()))
        self.bi.move_to_end(key, last=last)
        self.oracle.move_to_end(key, last=last)
        it = reversed if last else iter
        assert (key, val) == next(it(self.bi.items()))
        assert (val, key) == next(it(self.bi.inv.items()))
        assert (key, val) == next(it(self.oracle.data.items()))
        assert (val, key) == next(it(self.oracle.data_inv.items()))


BidictStateMachineTest = BidictStateMachine.TestCase


@pytest.mark.parametrize('bi_t', bidict_types)
def test_init_and_update_with_bad_args(bi_t: BT[KT, VT]) -> None:
    bad_args: t.Any
    for bad_args in ((None,), (0,), (False,), (True,), ({}, {})):
        # ty raises on unpacking an `Any`/unknown-length arg into a call; see
        # https://github.com/astral-sh/ty/issues/3649
        with pytest.raises(TypeError):
            bi_t(*bad_args)  # ty: ignore[invalid-argument-type, too-many-positional-arguments]
        if not issubclass(bi_t, MutableBidict):
            continue
        bi = bi_t()
        with pytest.raises(TypeError):
            bi.update(*bad_args)  # ty: ignore[invalid-argument-type, too-many-positional-arguments]  # https://github.com/astral-sh/ty/issues/3649


@pytest.mark.parametrize('bi_t', bidict_types)
def test_init_and_update_accept_legacy_sequence(bi_t: BT[t.Any, t.Any]) -> None:
    """Like dict, accept an arg that is iterable only via the legacy __getitem__ sequence protocol."""
    items = [(1, 'one'), (2, 'two')]
    # Typed Any since the type hints (like typeshed's for dict) only admit iterables that have __iter__.
    arg: t.Any = LegacySequence(items)
    expected = dict(arg)
    assert expected == dict(items)
    assert bi_t(arg) == expected
    if not issubclass(bi_t, MutableBidict):
        return
    for update in (bi_t.update, bi_t.forceupdate, bi_t.putall):
        bi = bi_t({0: 'zero'})
        update(bi, arg)
        assert bi == {0: 'zero', **expected}
        assert_bi_and_inv_are_inverse(bi)


@pytest.mark.parametrize('bi_t', bidict_types)
def test_init_and_update_accept_keys_via_getattr(bi_t: BT[t.Any, t.Any]) -> None:
    """Like dict, treat an arg as a mapping when it has keys(), even if only via __getattr__ (as a proxy's is)."""
    # Two-character keys would be silently split into bogus items, e.g. 'ab' -> ('a', 'b'),
    # if arg were mistaken for an iterable of items.
    arg: t.Any = KeysViaGetattr({'ab': 1, 'cd': 2})
    expected = dict(arg)
    assert expected == {'ab': 1, 'cd': 2}
    assert bi_t(arg) == expected
    assert list(inverted(arg)) == [(1, 'ab'), (2, 'cd')]
    if not issubclass(bi_t, MutableBidict):
        return
    for update in (bi_t.update, bi_t.forceupdate, bi_t.putall):
        bi = bi_t({'ef': 0})
        update(bi, arg)
        assert bi == {'ef': 0, **expected}
        assert_bi_and_inv_are_inverse(bi)


@pytest.mark.parametrize('bi_t', bidict_types)
def test_inv_attrs_readonly(bi_t: BT[KT, VT]) -> None:
    """Attempting to set .inverse or .inv should raise AttributeError."""
    bi: t.Any = bi_t()
    with pytest.raises(AttributeError):
        bi.inverse = 'foo'
    with pytest.raises(AttributeError):
        bi.inv = 'foo'


@pytest.mark.parametrize('bi_t', mutable_bidict_types)
def test_pop_missing_key(bi_t: MBT[t.Any, t.Any]) -> None:
    bi = bi_t()
    with pytest.raises(KeyError):
        bi.pop('foo')
    assert bi.pop('foo', 'bar') == 'bar'


@pytest.mark.parametrize('bi_t', [OrderedBidict, UserOrderedBi])
def test_move_to_end_missing_key(bi_t: type[OrderedBidict[KT, VT]]) -> None:
    bi = bi_t()
    with pytest.raises(KeyError):
        bi.move_to_end('foo')  # ty: ignore[invalid-argument-type]


@pytest.mark.parametrize('bi_t', bidict_types)
def test_eq_defers_to_other_eq(bi_t: BT[KT, VT]) -> None:
    """bidict.__eq__(other) should defer to other.__eq__ when other is not a mapping."""
    # ANY.__eq__ always returns true, so this test will fail if bi_t.__eq__ fails to defer.
    assert bi_t() == ANY


@pytest.mark.parametrize(('bi_t', 'non_mapping'), list(product(bidict_types, (None, 1, [], SupportsKeysAndGetItem({})))))
def test_eq_and_or_with_non_mapping(bi_t: BT[KT, VT], non_mapping: t.Any) -> None:
    bi = bi_t()
    assert bi != non_mapping
    assert not bi.equals_order_sensitive(non_mapping)
    with pytest.raises(TypeError):
        bi | non_mapping
    with pytest.raises(TypeError):
        non_mapping | bi


@given(items121=items121, bidict_t=bidict_t, rand=randoms())
def test_equals_order_sensitive(items121: Items121, bidict_t: BT[KT, VT], rand: Random) -> None:
    # Ensure there are at least 3 items in items121.
    items121.update({5: -5, 6: -6, 7: -7})
    bi = bidict_t(items121)
    items_shuf = list(items121.items())
    rand.shuffle(items_shuf)
    assume(not zip_equal(items_shuf, items121.items()))
    map_shuf = dict(items_shuf)
    assert bi == map_shuf
    assert not bi.equals_order_sensitive(map_shuf)


@given(items=items, bidict_t=bidict_t)
def test_inverted(items: Items, bidict_t: BT[int, int]) -> None:
    check = tuple(inverted(inverted(items)))
    expect = items
    assert check == expect
    items_nodup = dedup(items)
    check_bi = bidict_t(inverted(bidict_t(items_nodup)))
    expect_bi = bidict_t({v: k for (k, v) in items_nodup.items()})
    assert_bidicts_equal(check_bi, expect_bi)


@given(items=items, bidict_t=bidict_t)
# Pin the case that actually exercises the divergence, rather than relying on it being
# generated: (3, -1) overwrites (1, -1) in place, so an ordered bidict keeps the item's
# original position while its backing mappings append the new key and drop the old one.
@example(items=((1, -1), (2, -2), (3, -1)), bidict_t=UserOrderedBiBase)
def test_views_agree_with_iteration_order(items: Items, bidict_t: BT[int, int]) -> None:
    """Every order-sensitive API must agree with the bidict's own iteration order.

    For ordered bidicts the order lives in the linked list, not in the backing mappings,
    and the two diverge as soon as an item is overwritten -- including during __init__,
    for a type whose on_dup permits it. So the views must not delegate to _fwdm.
    """
    try:
        bi = bidict_t(items)
    except DuplicationError:  # this type's on_dup rejects these items; settle for a 1:1 init
        bi = bidict_t(dedup(items))
    expect = [(k, bi[k]) for k in bi]  # the items in iteration order, without using items()
    assert list(bi.keys()) == list(bi)
    assert list(bi.items()) == expect
    assert list(dict(bi)) == list(bi)  # dict(mapping) goes through keys()
    assert bi.equals_order_sensitive(bidict_t(expect))
    assert list(bi.values()) == [v for (_, v) in expect]
    assert list(bi.items()) == list(zip(bi.keys(), bi.values(), strict=True))
    if should_be_reversible(bidict_t):
        keysview, itemsview = bi.keys(), bi.items()
        assert isinstance(keysview, Reversible)
        assert isinstance(itemsview, Reversible)
        assert list(reversed(keysview)) == list(bi)[::-1]
        assert list(reversed(itemsview)) == expect[::-1]


@given(items121=items121)
def test_frozenbidicts_hashable(items121: Items121) -> None:
    """Frozen bidicts can be hashed (and therefore inserted into sets and mappings)."""
    bi = frozenbidict(items121)
    h1 = hash(bi)
    h2 = hash(bi)
    assert h1 == h2
    assert {bi}
    assert {bi: bi}
    bi2 = frozenbidict(items121)
    assert bi2 == bi
    assert hash(bi2) == h1


# These test cases ensure coverage of all the unwrite branches in [Ordered]BidictBase._write.
# (Hypothesis doesn't always generate examples that cover all the branches otherwise.)
@pytest.mark.parametrize(('bi_t', 'on_dup'), list(product(mutable_bidict_types, on_dups)))
def test_putall_matches_bulk_put(bi_t: type[MutableBidict[int, int]], on_dup: OnDup) -> None:
    for k1, v1, k2, v2 in product(range(4), repeat=4):
        for inv in False, True:
            # Start each case from the same state, so that each case reaches the branch it targets
            # (e.g. overwriting one key with a new value), rather than whatever earlier cases left behind.
            bi = bi_t({0: 0, 1: 1})
            assert_putall_matches_bulk_put(bi.inv if inv else bi, [(k1, v1), (k2, v2)], on_dup)


@pytest.mark.parametrize(('bi_t', 'on_dup'), list(product(mutable_bidict_types, on_dups)))
def test_putall_own_inverse(bi_t: type[MutableBidict[int, int]], on_dup: OnDup) -> None:
    """Updating from our own inverse must behave like updating from a snapshot of it, as b | b.inv does.

    The inverse shares our backing mappings, so this must not iterate over them while writing to them.
    """
    for init, inv in product(({0: 1, 2: 3}, {0: 1, 1: 2}), (False, True)):
        bi = bi_t(init)
        b = bi.inv if inv else bi
        expect = b.copy()
        assert_calls_match(
            partial(expect.putall, list(b.inv.items()), on_dup),
            partial(b.putall, b.inv, on_dup),
        )
        assert b.equals_order_sensitive(expect)
        assert b.inv.equals_order_sensitive(expect.inv)
        # b |= b.inv must agree with b = b | b.inv, as x |= y and x = x | y always do for a dict.
        bi = bi_t(init)
        b = bi.inv if inv else bi
        try:
            expect = b | b.inv
        except DuplicationError:
            expect = b.copy()
        assert_calls_match(partial(b.__or__, b.inv), partial(b.__ior__, b.inv))
        assert b.equals_order_sensitive(expect)
        assert b.inv.equals_order_sensitive(expect.inv)


def assert_putall_matches_bulk_put(bi: MutableBidict[int, int], new_items: Items, on_dup: OnDup) -> None:
    before = bi.copy()
    tmp = bi.copy()
    checkexc = None
    expectexc = None
    try:
        for key, val in new_items:
            tmp.put(key, val, on_dup)
    except DuplicationError as exc:
        expectexc = type(exc)
        tmp = before  # Since bulk updates fail clean, expect no changes (i.e. revert to before).
    try:
        bi.putall(new_items, on_dup)
    except DuplicationError as exc:
        checkexc = type(exc)
    assert checkexc == expectexc
    assert bi == tmp
    assert bi.inv == tmp.inv
    # == is order-insensitive, so it never walks an ordered bidict's linked list or node map.
    # (Only ordered bidicts promise to restore their order after a failed update.)
    if is_ordered(bi):
        assert bi.equals_order_sensitive(tmp)
        assert bi.inv.equals_order_sensitive(tmp.inv)


def assert_update_fails_clean(
    bi: MutableBidict[t.Any, t.Any],
    updates: t.Any,
    exc_t: type[BaseException] | tuple[type[BaseException], ...],
    on_dup: OnDup | None = None,
) -> None:
    """Check that a bulk update that raises *exc_t* leaves *bi* exactly as it was.

    Exercises update() (i.e. bi's own on_dup) when *on_dup* is None, else putall().
    """
    before = bi.copy()
    do_update = partial(bi.update, updates) if on_dup is None else partial(bi.putall, updates, on_dup)
    with pytest.raises(exc_t):
        do_update()
    assert bi.equals_order_sensitive(before)
    assert bi.inv.equals_order_sensitive(before.inv)


# A RAISE-free on_dup must fail clean too: a bulk update can raise for reasons that have
# nothing to do with duplication, so rollback cannot be conditioned on on_dup.
@pytest.mark.parametrize(('bi_t', 'on_dup'), list(product(mutable_bidict_types, (None, *on_dups))))
def test_update_with_bad_last_item_fails_clean(bi_t: MBT[t.Any, t.Any], on_dup: OnDup | None) -> None:
    bi = bi_t({
        0: 0,
        1: 1,
        2: 2,
    })
    for b in (bi, bi.inv):
        for exc, bad in BAD_ITEMS:
            # The items before the bad one are all new, so the update fails for the
            # bad item's reason regardless of the on_dup.
            updates = [(3, 3), (4, 4), bad]
            assert_update_fails_clean(b, updates, exc, on_dup)


@pytest.mark.parametrize('bi_t', [bidict, OrderedBidict])
@pytest.mark.parametrize(
    ('init', 'write', 'nwrites'),
    [
        # One case per kind of duplication BidictBase._write() handles, with the number of writes
        # to the backing mappings it performs: two to insert the new item, plus one to remove each
        # item that the new one displaces.
        ({1: 'a'}, lambda b: b.__setitem__(2, 'b'), 2),
        ({1: 'a'}, lambda b: b.__setitem__(1, 'z'), 3),
        ({1: 'a'}, lambda b: b.forceput(9, 'a'), 3),
        ({1: 'a', 2: 'b'}, lambda b: b.forceput(1, 'b'), 4),
    ],
    ids=['no-dup', 'dup-key', 'dup-val', 'dup-key-and-val'],
)
def test_write_fails_clean_when_a_backing_mapping_refuses(
    bi_t: MBT[t.Any, t.Any], init: dict[t.Any, t.Any], write: t.Any, nwrites: int
) -> None:
    """Writing one item must fail clean when a backing mapping refuses part-way through.

    _write() sets both backing mappings, and for some kinds of duplication deletes from them too.
    Backing mappings are user-supplied (see _fwdm_cls and _invm_cls), so any one of those writes
    can be refused, and everything already written must then be undone.
    """
    unchanged = dict(init), invdict(init)
    refused = 0
    for n in range(1, nwrites + 2):  # one past the last, which must find nothing left to refuse
        bi = bidict_refusing_nth_write(bi_t, init, n)
        try:
            write(bi)
        except WriteRefused:
            refused += 1
            assert (dict(bi._fwdm), dict(bi._invm)) == unchanged, f'refusing write #{n} left bi changed'
        else:
            break
    assert refused == nwrites


@pytest.mark.parametrize('bi_t', [bidict, OrderedBidict])
@pytest.mark.parametrize(
    ('remove', 'nwrites'),
    [
        # Removing an item takes two writes whichever way it is asked for: one to each
        # backing mapping.
        (lambda b: b.__delitem__(1), 2),
        (lambda b: b.pop(1), 2),
        (lambda b: b.popitem(), 2),
        # By a key equal to but distinct from the contained 1:
        (lambda b: b.__delitem__(1.0), 2),
        (lambda b: b.pop(True), 2),
    ],
    ids=['delitem', 'pop', 'popitem', 'delitem-equal-key', 'pop-equal-key'],
)
def test_remove_fails_clean_when_a_backing_mapping_refuses(bi_t: MBT[t.Any, t.Any], remove: t.Any, nwrites: int) -> None:
    """Removing an item must fail clean when a backing mapping refuses part-way through.

    The removing counterpart of test_write_fails_clean_when_a_backing_mapping_refuses:
    removing from one backing mapping and then being refused by the other must not leave
    the two disagreeing, nor holding a different key object than before, even when the
    removal was asked for by an equal but distinct key. An ordered bidict must also keep
    its order.
    """
    init = {1: 'a', 2: 'b'}
    unchanged = dict(init), invdict(init)
    refused = 0
    for n in range(1, nwrites + 2):  # one past the last, which must find nothing left to refuse
        bi = bidict_refusing_nth_write(bi_t, init, n)
        try:
            remove(bi)
        except WriteRefused:
            refused += 1
            assert (dict(bi._fwdm), dict(bi._invm)) == unchanged, f'refusing write #{n} left bi changed'
            assert all(bi._invm[v] is k for (k, v) in bi._fwdm.items()), f'refusing write #{n} replaced a key object'
            if bi_t is OrderedBidict:
                assert list(bi.items()) == list(init.items()), f'refusing write #{n} reordered bi'
        else:
            break
    assert refused == nwrites


@pytest.mark.parametrize('bi_t', [bidict, OrderedBidict])
@pytest.mark.parametrize('use_inv', [False, True], ids=['fwd', 'inv'])
@pytest.mark.parametrize(
    'remove',
    [lambda b: b.__delitem__(1), lambda b: b.pop(1), lambda b: b.popitem()],
    ids=['delitem', 'pop', 'popitem'],
)
def test_remove_fails_clean_when_the_value_stops_hashing(bi_t: MBT[t.Any, t.Any], use_inv: bool, remove: t.Any) -> None:
    """Removing an item whose value can no longer be hashed must fail clean.

    The value's hash is needed both to remove it from the backing mapping it is a key of, and to
    look up the contained key to put back when that removal fails, so the put-back must still
    restore the item when the lookup fails too. The item is inserted last so popitem() removes it.
    """
    val = HashFails()
    items = [('z', 'zz'), (1, val)]
    b = bi_t((v, k) for (k, v) in items) if use_inv else bi_t(items)
    bi = b.inverse if use_inv else b
    val.fail_after()
    with pytest.raises(HashFailed):
        remove(bi)
    val.stop()
    assert list(bi.items()) == items
    assert dict(bi._invm) == invdict(dict(bi._fwdm))
    assert all(bi.inverse[bi[k]] is k for k in bi)


@pytest.mark.parametrize('bi_t', [bidict, OrderedBidict])
@pytest.mark.parametrize(
    'update',
    [
        lambda b, arg: b.update(arg),
        lambda b, arg: b.forceupdate(arg),
        lambda b, arg: b.putall(arg),
        lambda b, arg: b.__ior__(arg),
    ],
    ids=['update', 'forceupdate', 'putall', 'ior'],
)
@pytest.mark.parametrize(
    ('init', 'arg'),
    [
        ({}, bidict({1: 'a', 2: 'b'})),  # empty and updating from a bidict: the _init_from() fast path
        # Otherwise _write() each item, recording unwrites.
        ({1: 'a'}, {2: 'b', 3: 'c'}),
        ({1: 'a', 2: 'b', 3: 'c'}, {4: 'd'}),
    ],
    ids=['from-bidict-into-empty', 'larger-than-self', 'smaller-than-self'],
)
def test_bulk_update_fails_clean_when_a_backing_mapping_refuses(
    bi_t: MBT[t.Any, t.Any], update: t.Any, init: dict[t.Any, t.Any], arg: Mapping[t.Any, t.Any]
) -> None:
    """A bulk update must fail clean when a backing mapping refuses part-way through, whichever way it is applied.

    The bulk counterpart of test_write_fails_clean_when_a_backing_mapping_refuses: _update()'s fast path
    writes to the backing mappings via _init_from() rather than _write(), and must not leave them disagreeing
    either. Refuses the nth write for each n in turn, until the update gets through.
    """
    unchanged = dict(init), invdict(init), list(init)
    refused = 0
    for n in range(1, 100):
        bi = bidict_refusing_nth_write(bi_t, init, n)
        try:
            update(bi, arg)
        except WriteRefused:
            refused += 1
            assert (dict(bi._fwdm), dict(bi._invm), list(bi)) == unchanged, f'refusing write #{n} left bi changed'
        else:
            break
    assert refused
    expected = init | dict(arg)
    assert (dict(bi._fwdm), dict(bi._invm), list(bi)) == (expected, invdict(expected), list(expected))


@pytest.mark.parametrize('bi_t', [bi_t for bi_t in mutable_bidict_types if issubclass(bi_t, OrderedBidictBase)])
@pytest.mark.parametrize(
    ('init', 'op'),
    [
        # k is the object whose hashing fails. The inv cases go through the inverse, whose nodes
        # are associated with its values rather than its keys.
        (lambda _: {0: 'a'}, lambda b, k: b.__setitem__(k, 'b')),
        (lambda _: {0: 'a'}, lambda b, k: b.putall([(k, 'b')])),
        (lambda _: {0: 'a'}, lambda b, k: b.inv.__setitem__('b', k)),
        (lambda k: {k: 'a', 0: 'b'}, lambda b, k: b.__setitem__(k, 'z')),
        (lambda k: {k: 'a', 0: 'b'}, lambda b, _: b.forceput(1, 'a')),
        (lambda k: {k: 'a', 0: 'b'}, lambda b, k: b.forceput(k, 'b')),
        (lambda k: {k: 'a', 0: 'b'}, lambda b, k: b.forceupdate({k: 'b'})),
        (lambda k: {k: 0, 'b': 1}, lambda b, k: b.inv.forceput(1, k)),
        (lambda k: {k: 'a', 0: 'b'}, lambda b, k: b.pop(k)),
        (lambda k: {k: 'a', 0: 'b'}, lambda b, k: b.__delitem__(k)),
        (lambda k: {k: 'a', 0: 'b'}, lambda b, _: b.inv.pop('a')),
        (lambda k: {0: 'b', k: 'a'}, lambda b, _: b.popitem()),
        (lambda k: {0: 'b', k: 'a'}, lambda b, _: b.inv.popitem()),
    ],
    ids=[
        'no-dup',
        'no-dup-putall',
        'no-dup-inv',
        'dup-key',
        'dup-val',
        'dup-key-and-val',
        'dup-key-and-val-forceupdate',
        'dup-key-and-val-inv',
        'pop',
        'delitem',
        'pop-inv',
        'popitem',
        'popitem-inv',
    ],
)
def test_ordered_write_and_remove_fail_clean_when_hashing_fails(
    bi_t: type[OrderedBidict[t.Any, t.Any]], init: t.Any, op: t.Any
) -> None:
    """An ordered bidict's write or removal must fail clean whichever of the times it hashes a key or value raises.

    Besides the backing mappings, an ordered bidict's linked list of nodes and its mapping from
    each contained key (or value) to its node must be left exactly as they were. Fails the nth
    hash of k for each n in turn, until the operation gets through.
    """
    k = HashFails()
    for n in count(1):
        bi = bi_t(init(k))
        before = list(bi.items()), dict(bi._fwdm), dict(bi._invm)
        k.fail_on(n)
        try:
            op(bi, k)
        except HashFailed:
            succeeded = False
        else:
            succeeded = True
        k.stop()
        if not succeeded:
            # items() walks the nodes, so this also catches orphaned or missing nodes.
            assert (list(bi.items()), dict(bi._fwdm), dict(bi._invm)) == before, f'failing hash #{n} left bi changed'
            assert all(bi._invm[v] is k_ for (k_, v) in before[0]), f'failing hash #{n} replaced a key object'
        assert list(bi.inv.items()) == [(v, k_) for (k_, v) in bi.items()]
        assert len(bi) == len(bi.inv) == len(list(bi))
        assert_orderedbidict_nodes_consistent(bi)
        assert_orderedbidict_nodes_consistent(bi.inv)
        if succeeded:
            break
    assert n > 1


@pytest.mark.parametrize('bi_t', [OrderedBidict, UserOrderedBi])
@pytest.mark.parametrize('use_inv', [False, True], ids=['fwd', 'inv'])
@pytest.mark.parametrize('method', ['pop', '__delitem__'])
def test_ordered_remove_fails_clean_when_hashing_the_value_keeps_failing(
    bi_t: type[OrderedBidict[t.Any, t.Any]], use_inv: bool, method: str
) -> None:
    """An ordered bidict's removal must fail clean when hashing the value being removed starts failing part-way through.

    Lets the first n hashes of the value succeed and fails every one after that, for each n in
    turn, until the removal gets through.
    """
    v = HashFails()
    for n in count():
        bi = bi_t({0: 'a', 1: v, 2: 'c'})
        before = list(bi.items())
        v.fail_after(n)
        try:
            if use_inv:
                getattr(bi.inv, method)(v)
            else:
                getattr(bi, method)(1)
        except HashFailed:
            succeeded = False
        else:
            succeeded = True
        v.stop()
        if not succeeded:
            assert list(bi.items()) == before, f'failing hash #{n + 1} left bi changed'
        assert len(bi) == len(list(bi)) == len(bi.inv) == len(list(bi.inv))
        assert_orderedbidict_nodes_consistent(bi)
        assert_orderedbidict_nodes_consistent(bi.inv)
        if succeeded:
            break
    assert n > 0
    assert list(bi.items()) == [(0, 'a'), (2, 'c')]


def _fill_empty(method: str, bi_t: MBT[t.Any, t.Any], items: t.Any, **kw: t.Any) -> t.Any:
    bi = bi_t()
    getattr(bi, method)(items, **kw)
    return bi


_FILLS_OF_EMPTY: t.Any = {
    'init': lambda bi_t, items: bi_t(items),
    'or': lambda bi_t, items: bi_t() | items,
    'ior': partial(_fill_empty, '__ior__'),
    'update': partial(_fill_empty, 'update'),
    'forceupdate': partial(_fill_empty, 'forceupdate'),
    **{f'putall-{od.key.name}-{od.val.name}': partial(_fill_empty, 'putall', on_dup=od) for od in on_dups},
}


@pytest.mark.parametrize('fill', _FILLS_OF_EMPTY.values(), ids=list(_FILLS_OF_EMPTY))
@pytest.mark.parametrize('side', ['_fwdm_cls', '_invm_cls'])
@pytest.mark.parametrize('base', [bidict, OrderedBidict])
def test_fill_from_bidict_checks_dups_by_own_backing_mappings(base: t.Any, side: str, fill: t.Any) -> None:
    """Filling an empty bidict from another bidict must match filling it from a dict of the same items.

    The other bidict has no dups as judged by its own backing mappings, but backing mappings are
    user-supplied (see _fwdm_cls and _invm_cls), so ours may judge some of its items equal.
    Skipping the dup check for them would collapse those items in only one of our backing mappings.
    """
    bi_t = type(f'CaseFolding{base.__name__}', (base,), {side: CaseFoldingDict})
    items = {'K': 'V', 'k': 'v'}  # one dup (of a key or a value, per side) once case is ignored

    def outcome(src: t.Any) -> t.Any:
        try:
            bi = fill(bi_t, src)
        except DuplicationError as exc:
            return type(exc)
        assert len(bi._fwdm) == len(bi._invm) == len(list(bi))
        return dict(bi._fwdm), dict(bi._invm), list(bi.items())

    assert outcome(bidict(items)) == outcome(dict(items))


#: (label, (mutation, expected items)) pairs, each acting on {'A': 1, 'B': 2} via the key 'a',
#: which only a case-insensitive backing mapping resolves to the contained key 'A'.
_CASE_FOLDING_KEY_OPS: t.Any = {
    'setitem': (lambda b: b.__setitem__('a', 3), [('A', 3), ('B', 2)]),
    'pop': (lambda b: b.pop('a'), [('B', 2)]),
    'delitem': (lambda b: b.__delitem__('a'), [('B', 2)]),
    'move_to_end': (lambda b: b.move_to_end('a'), [('B', 2), ('A', 1)]),
}


@pytest.mark.parametrize(('mutate', 'expected'), _CASE_FOLDING_KEY_OPS.values(), ids=list(_CASE_FOLDING_KEY_OPS))
@pytest.mark.parametrize('side', ['_fwdm_cls', '_invm_cls'])
def test_orderedbidict_acts_on_the_item_its_backing_mapping_resolves_to(
    side: str, mutate: t.Any, expected: list[tuple[str, int]]
) -> None:
    """An ordered bidict must act on the item that its (user-supplied) backing mapping resolves a key to.

    Its linked-list nodes are found via a plain dict, which may not resolve the key the same way.
    Both sides are covered, since through the inverse, the mapping resolving the key is _invm_cls.
    """
    bi_t = type('CaseFoldingOrderedBidict', (OrderedBidict,), {side: CaseFoldingDict})
    bi = bi_t({'A': 1, 'B': 2}) if side == '_fwdm_cls' else bi_t({1: 'A', 2: 'B'}).inverse
    mutate(bi)
    assert list(bi.items()) == expected
    assert list(bi.inverse.items()) == [(v, k) for (k, v) in expected]
    assert len(bi) == len(bi.inverse) == len(expected)


@pytest.mark.parametrize('bi_t', mutable_bidict_types)
@pytest.mark.parametrize('roundtrip', [copy, deepcopy, pickle_copy], ids=['copy', 'deepcopy', 'pickle'])
def test_roundtrip_preserves_iteration_order(bi_t: MBT[t.Any, t.Any], roundtrip: t.Any) -> None:
    """Duplicating a bidict must preserve its own iteration order.

    An ordered bidict preserves its inverse's order too, since both read the same linked list.
    A non-ordered one does not: its inverse gets rebuilt by inverting the forward mapping, which
    leaves it in the forward mapping's order -- the same thing that happens whenever a bidict is
    built from items, and the reason to reach for an OrderedBidict when order matters.
    """
    bi = bi_t({1: -1, 2: -2, 3: -3})
    bi.forceput(4, -2)  # a value-duplicating overwrite, which skews the inverse's order
    cp = roundtrip(bi)
    assert cp.equals_order_sensitive(bi)
    if isinstance(bi, OrderedBidictBase):
        assert cp.inv.equals_order_sensitive(bi.inv)


def test_pickle_preserves_order_of_generated_inverse_class() -> None:
    """An instance of a dynamically-generated inverse class keeps its own order.

    Such a class used to have no name pickle could reference it by, so __reduce__ pickled an
    instance of the class it was generated from and reconstructed this one by inverting, which
    left the order of the object being pickled derived rather than recorded. It is now pickled
    by reference like any other class (see _make_inv_cls), so the items are this object's own.
    """
    b: MutableBidict[t.Any, t.Any] = UserBiNotOwnInv()
    b.forceupdate([(1, 'a'), (2, 'b'), (3, 'a')])  # the last item skews the inverse's order
    inv = b.inverse
    assert list(inv.items()) == [('a', 3), ('b', 2)]
    roundtripped = pickle_copy(inv)
    assert type(roundtripped) is type(inv)
    assert roundtripped.equals_order_sensitive(inv)


def test_pickling_costs_no_extra_space() -> None:
    """Preserving the order must not have made pickles bigger.

    Recording the inverse's key order alongside the forward mapping would: measured at up to 150%
    more space, or ~10% more time once conditioned on actually being needed. Making the generated
    class referenceable instead costs neither, since only the forward items are ever written.
    """
    bi = bidict({i: -i for i in range(1000)})
    assert len(pickle.dumps(bi)) < len(pickle.dumps(dict(bi))) * 1.1


def test_pickle_orderedbi_whose_order_disagrees_with_fwdm() -> None:
    """An OrderedBidict whose order does not match its _fwdm's should pickle with the correct order."""
    ob = OrderedBidict({0: 1, 2: 3})
    # First get ob._fwdm's order to disagree with ob's:
    ob.inv[1] = 4
    assert list(ob.items()) == [(4, 1), (2, 3)]
    assert list(ob._fwdm.items()) == [(2, 3), (4, 1)]
    # Now check that its order is preserved after pickling and unpickling:
    roundtripped = pickle_copy(ob)
    assert list(roundtripped.items()) == [(4, 1), (2, 3)]
    assert roundtripped.equals_order_sensitive(ob)


def test_pickle_dynamically_generated_inverse_bidict() -> None:
    """Instances of dynamically-generated inverse bidict classes should be pickleable."""
    ub: MutableBidict[str, int] = UserBiNotOwnInv(one=1, two=2)
    roundtripped = pickle_copy(ub)
    assert roundtripped == ub == UserBiNotOwnInv({'one': 1, 'two': 2})
    assert dict(roundtripped) == dict(ub)
    # Now for the inverse:
    assert repr(ub.inverse) == "UserBiNotOwnInvInv({1: 'one', 2: 'two'})"
    # We can still pickle the inverse, even though its class, UserBiNotOwnInvInv, was
    # dynamically generated, and we didn't save a reference to it named "UserBiNotOwnInvInv"
    # anywhere that pickle could find it in sys.modules:
    for protocol in range(2, pickle.HIGHEST_PROTOCOL + 1):
        ubinv = pickle_copy(ub.inverse, protocol)
        assert repr(ubinv) == "UserBiNotOwnInvInv({1: 'one', 2: 'two'})"
    assert ub._inv_cls.__name__ not in (name for m in sys.modules for name in dir(m))
    # What pickle finds it by instead is its __qualname__, which spells out the attribute of
    # UserBiNotOwnInv that it is reachable through. Check that that lookup resolves back to it.
    assert ub._inv_cls.__qualname__ == 'UserBiNotOwnInv._inv_cls'
    module = sys.modules[ub._inv_cls.__module__]
    assert reduce(getattr, ub._inv_cls.__qualname__.split('.'), module) is ub._inv_cls


@pytest.mark.parametrize('bi_t', bidict_types)
def test_repr_with_indirect_self_reference(bi_t: BT[t.Any, t.Any]) -> None:
    """Where an item's repr includes the bidict (or its inverse), the bidict's repr must print a
    placeholder rather than recurse without end, as a dict's or an OrderedDict's does.

    A bidict can't contain itself, but it can contain such an item.
    """
    val = Handle()
    bi = bi_t({1: val})
    val.owner = bi
    assert repr(bi) == str(bi) == f'{bi_t.__name__}({{1: Handle(...)}})'
    for view in (bi.keys(), bi.values(), bi.items()):
        repr(view)  # (some views' reprs go through the bidict's)
    key = Handle()
    bi = bi_t({key: 1})
    key.owner = bi.inverse
    inv_name = type(bi.inverse).__name__
    assert repr(bi) == f'{bi_t.__name__}({{Handle({inv_name}({{1: Handle(...)}})): 1}})'


def test_abstract_bimap_init_fails() -> None:
    class AbstractBimap(BidirectionalMapping[t.Any, t.Any]):
        """Does not override `inverse` and therefore should not be instantiable."""

    for bi_t in (BidirectionalMapping, MutableBidirectionalMapping, AbstractBimap):
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            bi_t()


def test_bimap_bad_inverse() -> None:
    # Overrides `inverse`, but merely calls the abstract superclass implementation.
    class BimapBadInverse(BidirectionalMapping[t.Any, t.Any]):
        __getitem__ = __iter__ = __len__ = ...

        @property
        @override
        def inverse(self) -> t.Any:
            return super().inverse

    bi = BimapBadInverse()
    with pytest.raises(NotImplementedError):
        bi.inverse  # ruff: ignore[useless-expression]  # evaluating it is the point: it must raise


skip_if_pypy = pytest.mark.skipif(
    sys.implementation.name == 'pypy',
    reason='Requires CPython refcounting behavior',
)


@skip_if_pypy
@given(bidict_t=bidict_t)
def test_bidicts_freed_on_zero_refcount(bidict_t: BT[KT, VT]) -> None:
    """On CPython, the moment you have no more (strong) references to a bidict,
    there are no remaining (internal) strong references to it
    (i.e. no reference cycle was created between it and its inverse),
    allowing the memory to be reclaimed immediately, even with GC disabled.
    """
    gc.disable()
    try:
        bi = bidict_t()
        inv = bi.inverse  # The inverse is created lazily, so access it to give a cycle a chance to form.
        assert inv.inverse is bi
        weak, weakinv = weakref.ref(bi), weakref.ref(inv)
        assert weak() is not None
        assert weakinv() is not None
        del bi, inv
        assert weak() is None
        assert weakinv() is None
    finally:
        gc.enable()


@skip_if_pypy
@given(items121=items121)
def test_orderedbidict_nodes_freed_on_zero_refcount(items121: Items121) -> None:
    """On CPython, the moment you have no more references to an ordered bidict,
    the refcount of each of its internal nodes drops to 0
    (i.e. the linked list of nodes does not create a reference cycle),
    allowing the memory to be reclaimed immediately.
    """
    gc.disable()
    try:
        ob = OrderedBidict(items121)
        nodes = weakref.WeakSet(ob._sntl.iternodes())
        assert len(nodes) == len(ob)
        del ob
        assert len(nodes) == 0
    finally:
        gc.enable()


@given(items=items)
def test_orderedbidictbase_nodes_consistent(items: Items) -> None:
    """Complements the state machine's invariant for an immutable ordered bidict, which it doesn't cover."""
    assert_orderedbidict_nodes_consistent(UserOrderedBiBase(items))


def test_dict_subclass_backing_gets_native_views() -> None:
    """A backing dict subclass with dict views, e.g. OrderedDict, should get the same views a dict would.

    Those are reversible, carry a .mapping attribute, and implement their set operations in C,
    none of which a generic view over the bidict provides.
    """
    b = UserBiBackedByDictSub({1: 'one', 2: 'two'})  # backed by OrderedDict
    keysview, itemsview = b.keys(), b.items()
    assert not isinstance(keysview, BidictKeysView)  # the backing's own view, not a fallback
    assert isinstance(keysview, Reversible)
    assert isinstance(itemsview, Reversible)
    assert hasattr(keysview, 'mapping')
    assert hasattr(itemsview, 'mapping')
    assert list(reversed(keysview)) == [2, 1]
    assert list(reversed(itemsview)) == [(2, 'two'), (1, 'one')]
    # ...and the views still agree with the bidict itself.
    assert list(keysview) == list(b) == [1, 2]
    assert list(itemsview) == [(1, 'one'), (2, 'two')]
    assert keysview == {1, 2}
    assert list(b.values()) == ['one', 'two']


def test_non_dict_backing_falls_back_to_generic_views() -> None:
    """A backing mapping that is not a dict at all still gets a view over the bidict."""
    b = UserBi({1: 'one', 2: 'two'})  # backed by UserDict
    assert isinstance(b.keys(), BidictKeysView)
    assert list(b.keys()) == [1, 2]
    assert b.keys() == {1, 2}
    assert list(b.items()) == [(1, 'one'), (2, 'two')]


@pytest.mark.parametrize('bi_t', [UserBiBackedBySortedDict, UserOrderedBiBackedBySortedDict])
@pytest.mark.parametrize('viewname', ['keys', 'values', 'items'])
@pytest.mark.parametrize('set_op', SET_OPS)
def test_views_set_ops_match_dict_views_when_backing_has_own_views(
    bi_t: BT[t.Any, t.Any], viewname: str, set_op: t.Any
) -> None:
    """Set operations on a bidict's views must give what a dict's views give, down to the type of the result,
    even when its backing mapping is a dict subclass with views of its own.

    SortedDict's are an example: their set operations return a SortedSet, which raises TypeError for
    elements that cannot be ordered against each other, so the operand here includes such an element.
    """
    bi = bi_t({1: 'one', 2: 'two'})
    for b in (bi, bi.inverse):
        d = dict(b)
        # A dict's values() is not set-like, so compare with its inverse's keys().
        expect = invdict(d).keys() if viewname == 'values' else getattr(d, viewname)()
        # One element in common, and one that cannot be ordered against the others (a pair, for items()).
        other = {next(iter(expect)), (None, None) if viewname == 'items' else None}
        got, want = set_op(getattr(b, viewname)(), other), set_op(expect, other)
        assert (type(got), got) == (type(want), want)


def test_subclass_can_regain_reversibility() -> None:
    """A subclass whose backing mappings are reversible must be reversible.

    Regression test: _set_reversed() decided whether __reversed__ had been overridden by
    comparing the resolved value to BidictBase's. A class whose backing mappings are not
    reversible has __reversed__ set to None by _set_reversed() itself, and a subclass of
    it inherits that None, which compared unequal to BidictBase's and so was misread as a
    deliberate override -- leaving the subclass non-reversible no matter its own backings.
    """

    class NotReversible(bidict[t.Any, t.Any]):
        _fwdm_cls = UserDict
        _invm_cls = UserDict

    class ReversibleAgain(NotReversible):
        _fwdm_cls = dict
        _invm_cls = dict

    assert not issubclass(NotReversible, Reversible)  # UserDict is not reversible
    assert issubclass(ReversibleAgain, Reversible)  # but dict is
    bi = ReversibleAgain({1: 'one', 2: 'two'})
    assert list(reversed(bi)) == [2, 1]
    assert list(reversed(bi.keys())) == [2, 1]
    assert list(reversed(bi.values())) == ['two', 'one']


def test_user_provided_reversed_is_honored_and_inherited() -> None:
    """_set_reversed() must never clobber a __reversed__ that a user provided.

    This is what keeps OrderedBidict, which does not define __reversed__ itself, from
    computing one from its backing mappings and losing OrderedBidictBase's.
    """

    class CustomReversed(bidict[t.Any, t.Any]):
        @override
        def __reversed__(self) -> t.Any:
            return iter(['custom'])

    class SubCustom(CustomReversed):  # even with backings that are not reversible
        _fwdm_cls = UserDict
        _invm_cls = UserDict

    class Assigned(bidict[t.Any, t.Any]):
        pass

    Assigned.__reversed__ = vars(CustomReversed)['__reversed__']  # after _set_reversed() ran for Assigned

    class SubAssigned(Assigned):
        pass

    for bi_t in (CustomReversed, SubCustom, Assigned, SubAssigned):
        assert issubclass(bi_t, Reversible)
        assert list(reversed(bi_t())) == ['custom'], bi_t


@pytest.mark.parametrize(
    ('base', 'ordered_base'),
    [
        (bidict, OrderedBidict),
        (UserBi, OrderedBidict),
        (UserBiNotOwnInv, OrderedBidict),
        (frozenbidict, OrderedBidictBase),
    ],
)
def test_ordered_bidict_reverses_its_own_order_whatever_precedes_it(base: t.Any, ordered_base: t.Any) -> None:
    """An ordered bidict reverses its linked list, even with a non-ordered bidict class ahead of its ordered base
    in the MRO, whose own __reversed__ reverses its backing mapping (or is None, if that is not reversible).

    on_dup lets __init__ overwrite an item, which keeps its place in the linked list but not in the backing mappings.
    """
    ordered_t: t.Any = type('Ordered', (base, ordered_base), {'on_dup': ON_DUP_DROP_OLD})
    ob = ordered_t([(1, -1), (2, -2), (3, -1)])
    assert list(ob.items()) == [(3, -1), (2, -2)]
    for b in (ob, ob.inverse):
        assert isinstance(b, Reversible)
        assert list(reversed(b)) == list(b)[::-1]
        for view in (b.keys(), b.values(), b.items()):
            assert list(reversed(view)) == list(view)[::-1]


def test_reversed_opt_out_is_honored_wherever_it_is_declared() -> None:
    """A declared opt-out holds wherever it is in the MRO relative to a bidict class whose __reversed__
    is computed: after one (bidict, ahead of an opted-out ordered bidict class), or before one (a mixin).
    """

    class OptedOut(OrderedBidict[t.Any, t.Any]):
        __reversed__ = None

    class OptOutMixin:
        __reversed__ = None

    for bases in ((bidict, OptedOut), (OptOutMixin, bidict)):
        composed: t.Any = type('Composed', bases, {})
        assert not issubclass(composed, Reversible), bases
        with pytest.raises(TypeError):
            reversed(composed({1: -1}))


def test_set_reversed_is_idempotent() -> None:
    """Running _set_reversed() again must not make a computed __reversed__ look declared.

    It only runs once per class today, but were a repeat ever to take the class's own computed
    __reversed__ for a declared one, subclasses would inherit it rather than computing their own,
    which is exactly the bug that test_subclass_can_regain_reversibility covers.
    """

    class Computed(bidict[t.Any, t.Any]):
        pass

    Computed._set_reversed()

    class SubComputed(Computed):
        _fwdm_cls = UserDict
        _invm_cls = UserDict

    assert not issubclass(SubComputed, Reversible)  # still free to compute its own answer


def test_reversed_opt_out_is_honored_and_inherited() -> None:
    """Setting __reversed__ to None opts out of reversed(), for subclasses too.

    Unnecessary as of v0.22 for the usual case of non-reversible backing mappings, which
    _set_reversed() now detects, but still the way to opt out deliberately.
    """

    class OptedOut(bidict[t.Any, t.Any]):
        __reversed__ = None

    class SubOptedOut(OptedOut):
        pass

    for bi_t in (OptedOut, SubOptedOut):
        bi: t.Any = bi_t({1: 'one'})
        assert not isinstance(bi, Reversible), bi_t
        with pytest.raises(TypeError):
            reversed(bi)
        # The values view must not offer what the bidict itself declines to.
        assert not isinstance(bi.values(), Reversible), bi_t


@pytest.mark.parametrize('bi_t', [bi_t for bi_t in bidict_types if issubclass(bi_t, OrderedBidictBase)])
def test_orderedbidict_reversed_opt_out_is_honored_by_its_views(bi_t: t.Any) -> None:
    """An ordered bidict that opts out of reversed() cannot be reversed through its views either."""

    class OptedOut(bi_t):
        __reversed__ = None

    ob: t.Any = OptedOut({1: 'one'})
    assert not isinstance(ob, Reversible)
    for b in (ob, ob.inverse):
        for view in (b.keys(), b.values(), b.items()):
            assert not isinstance(view, Reversible), view  # never advertising a reversed() that raises
            with pytest.raises(TypeError):  # and the claim is not a lie
                reversed(view)


def test_orderedbidict_reversed_opt_out_after_class_creation_is_honored_by_its_views() -> None:
    """An ordered bidict whose class opts out of reversed() after it was created cannot be reversed through
    its views either, although the views' classes, unlike the bidict's, still claim to be Reversible.
    """

    class OptedOutLater(OrderedBidict[t.Any, t.Any]):
        pass

    # The declared type of OrderedBidictBase.__reversed__ doesn't allow opting out after creation, which this tests.
    OptedOutLater.__reversed__ = t.cast('t.Any', None)
    ob = OptedOutLater({1: 'one'})
    for b in (ob, ob.inverse):
        for view in (b, b.keys(), b.values(), b.items()):
            with pytest.raises(TypeError):
                reversed(view)


@pytest.mark.parametrize('bi_t', bidict_types)
def test_class_keywords_reach_later_base(bi_t: t.Any) -> None:
    """Class keyword arguments pass through a bidict base to a later base that accepts them, as through dict.

    Parametrized over bidict_types to cover a class whose inverse class is generated (UserBiNotOwnInv),
    which, like any other subclass, isn't passed them.
    """

    class Labeled:
        label: t.ClassVar[str]

        def __init_subclass__(cls, label: str = '', **kw: t.Any) -> None:
            super().__init_subclass__(**kw)
            cls.label = label

    class Sub(bi_t, Labeled, label='sub'):
        pass

    assert Sub.label == 'sub'
    bi = Sub({1: -1})
    assert bi.inverse[-1] == 1
    assert type(bi.inverse.inverse) is Sub
    assert type(bi.inverse).label == ('sub' if type(bi.inverse) is Sub else '')


#: Ways to mutate an ordered bidict, keyed by name. Each takes the bidict and the key
#: just yielded by the iteration in progress.
_MUTATIONS_DURING_ITERATION: t.Any = {
    'insert': lambda ob, key: ob.__setitem__(f'new{key}', f'new{key}'),
    'delete': lambda ob, key: ob.pop(next(k for k in ob if k != key), None),
    'clear': lambda ob, _key: ob.clear(),
    'move_to_end': lambda ob, key: ob.move_to_end(key),
    'collapse_to_fewer_items': lambda ob, key: ob.forceput(key, next(iter(ob.inv))),
    'insert_via_the_inverse': lambda ob, key: ob.inv.__setitem__(f'new{key}', f'new{key}'),
    'replace_key_in_place': lambda ob, key: ob.forceput(f'new{key}', ob[key]),
    'replace_key_via_the_inverse': lambda ob, key: ob.inv.__setitem__(ob[key], f'new{key}'),
}


def _iterate_while_mutating(ob: OrderedBidict[t.Any, t.Any], iterate: t.Any, mutate: t.Any) -> None:
    """Iterate *ob* via *iterate*, applying *mutate* to it on each step.

    Bounded, so that a failure to detect the mutation fails the test rather than hanging it:
    inserting during iteration used to grow the linked list ahead of the iterator forever.
    """
    for i, key in enumerate(iterate(ob)):
        assert i < 100, 'iteration did not terminate after mutation'
        mutate(ob, key)


@pytest.mark.parametrize('mutate', _MUTATIONS_DURING_ITERATION.values(), ids=list(_MUTATIONS_DURING_ITERATION))
@pytest.mark.parametrize('iterate', [iter, reversed], ids=['forward', 'reverse'])
def test_orderedbidict_mutation_during_iteration_raises(mutate: t.Any, iterate: t.Any) -> None:
    """Mutating an ordered bidict while iterating it must raise RuntimeError.

    dict and OrderedDict both do this. Without it, inserting during iteration looped forever,
    clear() raised a KeyError naming an internal Node, and deleting silently skipped items.
    Note the *_via_the_inverse mutations go through the inverse, which shares the linked list,
    so they must invalidate this iterator too.
    """
    ob: OrderedBidict[t.Any, t.Any] = OrderedBidict({1: 'one', 2: 'two', 3: 'three'})
    with pytest.raises(RuntimeError):
        _iterate_while_mutating(ob, iterate, mutate)


def test_orderedbidict_mutation_on_final_item_raises() -> None:
    """Mutating while the last item is being visited raises, unlike OrderedDict.

    dict raises here and OrderedDict does not, so the two disagree and we cannot match both.
    Raising is the safer of the two, keeps OrderedBidict consistent with plain bidict (which
    is backed by a dict and so already raises), and avoids code that works or not depending
    on which iteration the mutating branch happens to be taken on.
    """
    ob = OrderedBidict({1: 'one', 2: 'two'})
    with pytest.raises(RuntimeError):
        _iterate_while_mutating(ob, iter, lambda o, key: o.__setitem__(3, 'three') if key == 2 else None)


@pytest.mark.parametrize('inv', [False, True], ids=['fwd', 'inv'])
@pytest.mark.parametrize('view', [None, 'keys', 'items', 'values'])
@pytest.mark.parametrize('iterate', [iter, reversed], ids=['forward', 'reverse'])
def test_orderedbidict_iteration_allows_value_only_update(iterate: t.Any, view: str | None, inv: bool) -> None:
    """Updating an existing key's value changes none of the keys being iterated, so it must not raise.

    dict and OrderedDict both permit this, and an ordered bidict's iteration order is
    unaffected by it: the item keeps its node, and so its position. This holds for the
    values view too, even though its elements are the inverse's keys, which such an
    update does replace.
    """
    ob = OrderedBidict({1: 'one', 2: 'two'})
    b: OrderedBidict[t.Any, t.Any] = ob.inverse if inv else ob
    keys = list(b)
    new_vals = [10, 11] if inv else ['updated0', 'updated1']
    visited = 0
    for _ in iterate(b if view is None else getattr(b, view)()):
        b[keys[visited]] = new_vals[visited]
        visited += 1
    assert visited == len(keys)
    assert list(b.items()) == list(zip(keys, new_vals, strict=True))


#: Bulk updates that pass more items than the bidict contains but change no keys: either
#: nothing at all, or only the value of the item just yielded. Each takes the bidict and that key.
_BULK_UPDATES_CHANGING_NO_KEYS: t.Any = {
    'update_no_op': lambda b, key: b.update([*b.items(), (key, b[key])]),
    'update_value_only': lambda b, key: b.update([*b.items(), (key, f'new{key}')]),
    'forceupdate_value_only': lambda b, key: b.forceupdate([*b.items(), (key, f'new{key}')]),
    'putall_no_op': lambda b, key: b.putall([*b.items(), (key, b[key])]),
}


@pytest.mark.parametrize('mutate', _BULK_UPDATES_CHANGING_NO_KEYS.values(), ids=list(_BULK_UPDATES_CHANGING_NO_KEYS))
@pytest.mark.parametrize(
    ('bi_t', 'iterate'),
    [
        (bi_t, iterate)
        for bi_t in mutable_bidict_types
        for iterate in (iter, reversed)
        if iterate is iter or should_be_reversible(bi_t)
    ],
)
def test_iteration_allows_bulk_update_changing_no_keys(bi_t: MBT[t.Any, t.Any], iterate: t.Any, mutate: t.Any) -> None:
    """A bulk update that changes no keys must not disturb a live iterator, as with dict and OrderedDict.

    Deleting some items first leaves holes in the backing dicts, which an update that rebuilt them would close.
    """
    bi = bi_t({i: -i for i in range(10)})
    for i in range(7):
        del bi[i]
    keys = []
    for key in iterate(bi):
        assert len(keys) < 100, 'iteration did not terminate'
        mutate(bi, key)
        keys.append(key)
    assert keys == list(iterate(bi)) == list(iterate([7, 8, 9]))


#: Changes to the keys of an ordered bidict *b* (which may itself be an inverse). The last two replace a
#: key in place: the item keeps its node, so the linked list is not restructured, but b's keys change.
_KEY_CHANGES: t.Any = {
    'insert': lambda b: b.__setitem__(object(), object()),
    'replace_key_in_place': lambda b: b.forceput(object(), next(iter(b.values()))),
    'replace_key_via_the_inverse': lambda b: b.inverse.__setitem__(next(iter(b.values())), object()),
}


@pytest.mark.parametrize('mutate', _KEY_CHANGES.values(), ids=list(_KEY_CHANGES))
@pytest.mark.parametrize('inv', [False, True], ids=['fwd', 'inv'])
@pytest.mark.parametrize('bi_t', [OrderedBidict, UserOrderedBi])
@pytest.mark.parametrize('view', [None, 'keys', 'items', 'values'])
@pytest.mark.parametrize('iterate', [iter, reversed], ids=['forward', 'reverse'])
def test_orderedbidict_iterator_created_before_mutation_raises(
    bi_t: type[OrderedBidict[int, str]], view: str | None, iterate: t.Any, inv: bool, mutate: t.Any
) -> None:
    """The check must catch a mutation made after the iterator was created but before it ran.

    OrderedDict does this too, which is why iteration, including via the keys(), values(), and
    items() views, captures the version eagerly rather than on the first next() call.
    Replacing a key in place must be caught too, whichever direction the write goes through,
    even though a bidict and its inverse share one linked list, and to the other direction
    the same write only replaces a value.
    """
    ob = bi_t({1: 'one', 2: 'two'})
    b: OrderedBidict[t.Any, t.Any] = ob.inverse if inv else ob
    it = iterate(b if view is None else getattr(b, view)())
    mutate(b)
    with pytest.raises(RuntimeError):
        list(it)


#: (items, call) pairs, each call leaving an ordered bidict exactly as it was.
_NO_OP_MUTATIONS: t.Any = {
    'move_last_to_end': ({1: 'one', 2: 'two'}, lambda ob: ob.move_to_end(2)),
    'move_first_to_start': ({1: 'one', 2: 'two'}, lambda ob: ob.move_to_end(1, last=False)),
    'move_last_to_end_via_the_inverse': ({1: 'one', 2: 'two'}, lambda ob: ob.inv.move_to_end('two')),
    'move_only_item_to_start': ({1: 'one'}, lambda ob: ob.move_to_end(1, last=False)),
    'clear_when_empty': ({}, lambda ob: ob.clear()),
}


@pytest.mark.parametrize(('items', 'call'), _NO_OP_MUTATIONS.values(), ids=list(_NO_OP_MUTATIONS))
@pytest.mark.parametrize('inv', [False, True], ids=['fwd', 'inv'])
@pytest.mark.parametrize('bi_t', [OrderedBidict, UserOrderedBi])
@pytest.mark.parametrize('view', [None, 'keys', 'items', 'values'])
@pytest.mark.parametrize('iterate', [iter, reversed], ids=['forward', 'reverse'])
def test_orderedbidict_no_op_does_not_invalidate_iterators(
    items: dict[int, str], call: t.Any, inv: bool, bi_t: type[OrderedBidict[int, str]], view: str | None, iterate: t.Any
) -> None:
    """A call that changes nothing must not invalidate iterators.

    OrderedDict permits a move_to_end() of an item already at the requested end, and dict,
    OrderedDict, and bidict all permit a clear() when already empty. The former supports e.g.
    LRU-style code that touches the most recently used item while iterating.
    """
    ob = bi_t(items)
    b: OrderedBidict[t.Any, t.Any] = ob.inverse if inv else ob

    def iterate_b(_: t.Any) -> t.Any:
        return iterate(b if view is None else getattr(b, view)())

    expected = list(iterate_b(b))
    it = iterate_b(b)
    call(ob)  # before the first next() call
    assert list(it) == expected
    _iterate_while_mutating(ob, iterate_b, lambda o, _key: call(o))
    assert list(ob.items()) == list(items.items())


def test_orderedbidict_iteration_unaffected_by_unrelated_bidict() -> None:
    """Only mutations to *this* bidict's linked list invalidate its iterators."""
    ob, other = OrderedBidict({1: 'one', 2: 'two'}), OrderedBidict({3: 'three'})
    keys = []
    for key in ob:
        other[key] = f'x{key}'  # a different bidict, so a different linked list
        keys.append(key)
    assert keys == [1, 2]


def _failed_inverse_collapse(b: t.Any) -> None:
    """Collapse two items through the inverse in an update that then fails, and so is rolled back."""
    with pytest.raises(TypeError):
        b.inverse.forceupdate([(Tagged(2, 'new'), Tagged(3, 'new')), ('x', [])])  # [] is unhashable
    assert all(x.tag == 'orig' for item in b.items() for x in item), 'rollback did not restore the contained objects'


#: (label, mutation) pairs, each writing an item that duplicates a contained key, a contained
#: value, or both, using an object that is equal to the contained one but not identical to it.
#: Some write through the inverse, since an ordered bidict's inverse finds nodes by value.
_DUPLICATING_WRITES: t.Any = {
    'key_duplication': lambda b: b.__setitem__(Tagged(1, 'new'), 'other'),
    'value_duplication': lambda b: b.forceput(Tagged(9, 'new'), Tagged(2, 'new')),
    'collapse': lambda b: b.forceput(Tagged(1, 'new'), Tagged(4, 'new')),
    'inverse_key_duplication': lambda b: b.inverse.__setitem__(Tagged(2, 'new'), 'other'),
    'inverse_value_duplication': lambda b: b.inverse.forceput(Tagged(9, 'new'), Tagged(1, 'new')),
    'inverse_collapse': lambda b: b.inverse.forceput(Tagged(2, 'new'), Tagged(3, 'new')),
    'inverse_collapse_forceupdate': lambda b: b.inverse.forceupdate([(Tagged(2, 'new'), Tagged(3, 'new'))]),
    'inverse_collapse_rolled_back': _failed_inverse_collapse,
}


@pytest.mark.parametrize('mutate', _DUPLICATING_WRITES.values(), ids=list(_DUPLICATING_WRITES))
@pytest.mark.parametrize('bi_t', mutable_bidict_types)
def test_one_object_per_item_in_both_directions(bi_t: MBT[t.Any, t.Any], mutate: t.Any) -> None:
    """A bidict and its inverse must hold the same object for each item, not equal copies.

    dict keeps the key object it already has when a key is overwritten, but takes the new
    value object. In a bidict a value is also a key of the inverse, so those two conventions
    conflict; a write given an object equal to but distinct from a contained key or value keeps
    the contained object in both backing mappings, so that b.inverse[b[key]] is key still holds.
    The bidict starts with two items so that a write can also collapse them into one.
    """
    bi = bi_t({Tagged(1, 'orig'): Tagged(2, 'orig'), Tagged(3, 'orig'): Tagged(4, 'orig')})
    mutate(bi)
    for key in bi:
        val = bi[key]
        assert bi.inverse[val] is key, 'key differs between a bidict and its inverse'
        inv_key = next(k for k in bi.inverse if k == val)
        assert inv_key is val, 'value differs between a bidict and its inverse'


@pytest.mark.parametrize('bi_t', mutable_bidict_types)
def test_duplicating_write_keeps_the_contained_object(bi_t: MBT[t.Any, t.Any]) -> None:
    """Of two equal objects, the one already contained is the one kept.

    That is what a dict does for keys, and it is the only self-consistent choice here:
    adopting the incoming key object instead would mean deleting and reinserting it, which
    would move the item to the end and so silently reorder the bidict.
    """
    bi = bi_t({Tagged(1, 'orig'): Tagged(2, 'orig')})
    bi[Tagged(1, 'new')] = Tagged(3, 'new')  # key duplicates the contained Tagged(1)
    (key,) = bi
    assert key.tag == 'orig'
    assert bi.inverse[bi[key]].tag == 'orig'


@pytest.mark.parametrize('bi_t', mutable_bidict_types)
def test_duplicating_write_does_not_reorder(bi_t: MBT[t.Any, t.Any]) -> None:
    """Keeping the contained key object also keeps the item in place."""
    bi = bi_t({Tagged(1): 'one', Tagged(2): 'two'})
    bi[Tagged(1, 'new')] = 'uno'
    assert [k.n for k in bi] == [1, 2]


def test_orderedbidict_weakattr_class_access() -> None:
    """Accessing a WeakAttr descriptor from the Node class should return the descriptor itself."""
    descriptor = OrderedBidictNode.prv
    assert isinstance(descriptor, WeakAttr)


def test_orderedbidictbase_order_diverges_from_backing_mappings() -> None:
    """Spell out the scenario behind test_views_agree_with_iteration_order's @example.

    That test checks the views against the bidict's own iteration order, so on its own it
    could not tell you whether the two orders ever actually differ. This pins that they do,
    with absolute expectations, and covers repr() (which goes through items()) besides.

    Regression test: the keys()/items() overrides used to live on OrderedBidict, justified
    by a *mutable* ordered bidict getting out of sync with its backing mappings after
    mutation. But an overwrite during __init__ suffices, so OrderedBidictBase needs them too.
    """
    ob = UserOrderedBiBase([(1, 'a'), (2, 'b'), (3, 'a')])  # (3, 'a') overwrites (1, 'a') in place
    assert list(ob) == [3, 2]  # the item formerly keyed 1 is now keyed 3, in its original position
    assert list(ob._fwdm) == [2, 3]  # whereas the backing dict appended 3 and dropped 1
    assert repr(ob) == "UserOrderedBiBase({3: 'a', 2: 'b'})"


def test_orderedbidict_cross_view_set_operations() -> None:
    """Set operations between an OrderedBidict keys view and an items view (or vice versa) should
    behave like the equivalent plain dict views rather than raising TypeError or giving a wrong result.
    """
    ob1 = OrderedBidict({'a': 1, 'b': 2})
    ob2 = OrderedBidict({'a': 1})
    d1 = {'a': 1, 'b': 2}
    d2 = {'a': 1}
    # The comparison operators return bools; the set-algebra operators return sets/bools. In every
    # case the OrderedBidict view result must match the equivalent plain dict view result exactly.
    # fmt: off
    ops = (
        '__lt__', '__le__', '__gt__', '__ge__', '__eq__', '__ne__',  # comparisons
        '__sub__', '__or__', '__xor__', '__and__', 'isdisjoint',  # set algebra
    )
    # fmt: on
    for op in ops:
        assert getattr(ob1.keys(), op)(ob2.items()) == getattr(d1.keys(), op)(d2.items()), op
        assert getattr(ob1.items(), op)(ob2.keys()) == getattr(d1.items(), op)(d2.keys()), op


@pytest.mark.parametrize('bi_t', bidict_types)
def test_items_view_membership_matches_dict_items(bi_t: BT[t.Any, t.Any]) -> None:
    """`x in b.items()` must agree with a dict's items view for any x, not just for (key, value) pairs.

    For anything but a 2-tuple, e.g. 'kv', [key, value], 1, or (1, 2, 3), that means False, not a
    match against its elements or an unpacking error, including when a Set comparison checks it,
    whatever the bidict's backing mappings. For a pair, it means comparing the contained value to the
    given one as dict_items does: identity first (so a contained nan matches itself), then with the
    contained value on the left (so it matches an AsymLookup that a contained AsymStored equals).
    """
    nan, stored = float('nan'), AsymStored()
    d = {'k': 'v', 1: 2, 'n': nan, 's': stored, nan: 'nk', stored: 'sk'}
    bi = bi_t(d)
    probes = (
        *('kv', 'vk', [1, 2], [2, 1], 1, None, (), (1,), (1, 2, 3), ('k', 'v'), (1, 2), (2, 1), ([1], 2)),
        *(('n', nan), ('s', AsymLookup()), ('nk', nan), ('sk', AsymLookup())),
    )
    non_pairs = KeysView(UserDict({1: 1}))  # a Set that is not a dict view, whose elements are not pairs
    for b, items in ((bi, d), (bi.inverse, invdict(d))):
        view = b.items()
        expect = items.items()
        for probe in probes:
            assert_calls_match(partial(operator.contains, view, probe), partial(operator.contains, expect, probe))
        assert_calls_match(partial(operator.le, non_pairs, view), partial(operator.le, non_pairs, expect))
        assert_calls_match(partial(operator.ge, view, non_pairs), partial(operator.ge, expect, non_pairs))


@pytest.mark.parametrize('bi_t', bidict_types)
def test_views_read_backing_mappings_not_subclass_overrides(bi_t: t.Any) -> None:
    """Like a dict subclass's views, a bidict's views read its backing mappings directly,
    not through a subclass's __len__, __contains__, or __getitem__,
    and so neither do repr() and the other methods that use items().
    """

    class Overrides(bi_t):
        @override
        def __len__(self) -> int:
            return 99

        @override
        def __contains__(self, key: object) -> bool:
            return True

        @override
        def __getitem__(self, key: t.Any) -> t.Any:
            return 'overridden'

    d = {1: 'a', 2: 'b'}
    bi = Overrides(d)
    for b, items in ((bi, d), (bi.inverse, invdict(d))):
        # The overrides are in effect on the bidict itself, but not on its views, which agree with a dict's.
        assert (len(b), 'absent' in b, b[next(iter(items))]) == (99, True, 'overridden')
        for viewname, absent in (('keys', 'absent'), ('values', 'absent'), ('items', ('absent', 'absent'))):
            view, expect = getattr(b, viewname)(), getattr(items, viewname)()
            assert len(view) == len(expect)
            assert list(view) == list(expect)
            assert all(x in view for x in expect)
            assert absent not in view
            if isinstance(view, Reversible):
                assert list(reversed(view)) == list(reversed(expect))
        assert repr(b) == f'{type(b).__name__}({items})'


def test_abc_slots() -> None:
    """Bidict ABCs should define __slots__.

    Ref: https://docs.python.org/3/reference/datamodel.html#notes-on-using-slots

    Note: non-abstract bidict types do not define __slots__ as of v0.22.0.
    """
    assert BidirectionalMapping.__dict__['__slots__'] == ()
    assert MutableBidirectionalMapping.__dict__['__slots__'] == ()


@pytest.mark.parametrize('viewname', ['keys', 'items'])
@pytest.mark.parametrize('bi_t', mutable_bidict_types)
def test_view_iterator_detects_mutation_before_first_next(bi_t: MBT[t.Any, t.Any], viewname: str) -> None:
    """An iterator over a bidict's keys() or items() view (or its inverse's) raises RuntimeError if the bidict
    changes size between the iterator's creation and its first next() call, as a dict view's iterator does,
    whether or not the bidict is reversible.
    """
    bi = bi_t({1: -1, 2: -2})
    for b in (bi, bi.inverse):
        it = iter(getattr(b, viewname)())
        bi[len(bi) + 1] = -len(bi) - 1
        with pytest.raises(RuntimeError):
            next(it)


@pytest.mark.parametrize('bi_t', bidict_types)
@pytest.mark.parametrize('opt_out', [False, True], ids=['as_is', 'opted_out'])
def test_views_have_no_instance_dict(bi_t: BT[t.Any, t.Any], opt_out: bool) -> None:
    """Like dict views, bidict's own views have no per-instance __dict__.

    A view class's __slots__ = () only takes effect if every class in its MRO declares __slots__.
    Views that a backing mapping provides are its own business (on PyPy, OrderedDict's have a __dict__).
    A bidict that opts out of reversed() gets non-reversible variants of its views, so check those too.
    """
    if opt_out:
        bi_t = type('OptedOut', (bi_t,), {'__reversed__': None})
    bi = bi_t({1: 'one'})
    for b in (bi, bi.inverse):
        for view in (b.keys(), b.values(), b.items()):
            if type(view).__module__.partition('.')[0] == 'bidict':
                assert not hasattr(view, '__dict__'), type(view)


@pytest.mark.parametrize('bi_t', bidict_types)
def test_views_reversibility_matches_bidict(bi_t: BT[t.Any, t.Any]) -> None:
    """keys(), values(), and items() must each be reversible when the bidict itself is, and those
    that bidict provides must not be when it isn't -- never advertising a reversed() that raises.

    A dict-backed bidict's keys() and items() are its backing dict's own views, which reverse correctly.
    """
    bi = bi_t({1: -1, 2: -2})
    for b in (bi, bi.inverse):
        if isinstance(b, Reversible):
            for view in (b.keys(), b.values(), b.items()):
                assert isinstance(view, Reversible), view
                assert list(reversed(view)) == list(view)[::-1]
        else:
            for view in (b.values(),) if b._fwdm_has_dict_views else (b.keys(), b.values(), b.items()):
                assert not isinstance(view, Reversible), view
                with pytest.raises(TypeError):  # and the claim is not a lie
                    reversed(t.cast('t.Any', view))


def test_views_of_bidict_declaring_reversed_are_reversible() -> None:
    """A bidict that declares __reversed__ is reversible whatever its backing mappings, and so are its views."""

    class DeclaresReversed(bidict[t.Any, t.Any]):
        _fwdm_cls = UserDict
        _invm_cls = UserDict

        @override
        def __reversed__(self) -> t.Any:
            return reversed(list(self))

    bi = DeclaresReversed({1: -1, 2: -2})
    for b in (bi, bi.inverse):
        for view in (b.keys(), b.values(), b.items()):
            assert isinstance(view, Reversible), view
            assert list(reversed(view)) == list(view)[::-1]


@given(items121=items121)
@pytest.mark.parametrize('bi_t', [UserBiBackedByReversibleNonDict, UserBiBackedByReversibleValues])
def test_reversed_values_with_reversible_userdict(bi_t: MBT[int, int], items121: Items121) -> None:
    """A reversible mapping need not return a reversible values view, though it may."""
    bi = bi_t(items121)
    for current in (bi, bi.inverse):
        values = current.values()
        assert isinstance(values, Reversible)
        assert list(reversed(values)) == list(values)[::-1]
        # Capture the backing iterator now, not on the first next() call.
        iterator = reversed(values)
        current[1000] = -1000
        with pytest.raises(RuntimeError):
            next(iterator)


@pytest.mark.parametrize('bi_t', bidict_types)
def test_values_view_repr_shows_its_bidict(bi_t: BT[t.Any, t.Any]) -> None:
    """A values view's repr shows the bidict whose values it views, as ValuesView's does,
    and so lists them in the order the view yields them.

    Overwriting key 1's value moves it to the end of the backing inverse mapping but not of
    the forward one, so the inverse lists the values in a different order.
    """
    bi = bi_t([(1, 'a'), (2, 'b'), (1, 'c')])
    for b in (bi, bi.inverse):
        view = b.values()
        assert repr(view) == f'{type(view).__name__}({b!r})'


@pytest.mark.parametrize('bi_t', bidict_types)
def test_inv_aliases_inverse(bi_t: BT[KT, VT]) -> None:
    """bi.inv should alias bi.inverse."""
    bi = bi_t()
    assert bi.inverse is bi.inv
    assert bi.inv.inverse is bi.inverse.inv


def test_static_types() -> None:
    d = {'1': 1}
    fb = frozenbidict(d)
    assert_type(fb, frozenbidict[str, int])
    assert_type(fb.inv, frozenbidict[int, str])
    # reversed() yields keys, whatever their type.
    assert_type(reversed(fb), Iterator[str])
    assert_type(reversed(fb.inv), Iterator[int])
    # An ordered bidict's views are reversible, like an OrderedDict's.
    ob = OrderedBidict(d)
    assert_type(reversed(ob.keys()), Iterator[str])
    assert_type(reversed(ob.values()), Iterator[int])
    assert_type(reversed(ob.items()), Iterator[tuple[str, int]])


@pytest.mark.parametrize('bi_t', bidict_types)
def test_get_type_hints(bi_t: t.Any) -> None:
    """typing.get_type_hints() resolves the annotations of every class in a bidict subclass's MRO.

    It looks each class's annotations up in the module that the class's __module__ names, which for
    the classes that bidict exports is not the module that defined them (see bidict/__init__.py).
    """

    class Sub(bi_t):
        note: str

    assert t.get_type_hints(Sub)['note'] is str


@pytest.mark.parametrize('bi_t', mutable_bidict_types)
def test_setitem_existing_is_noop_with_nonreflexive_eq(bi_t: MBT[t.Any, t.Any]) -> None:
    """Setting an existing (key, val) pair should be a no-op even when key == key is False.

    Float NaN has non-reflexive equality (nan != nan), so it exercises
    the identity-based same-item check in _dedup.

    (Previously, _dedup used an equality-based same-item check that caused
    spurious KeyAndValueDuplicationErrors and AssertionErrors. See #377.)
    """
    nan = float('nan')
    # NaN as key: b[nan] = 'a' again must not raise
    b1 = bi_t()
    b1[nan] = 'a'
    b1[nan] = 'a'
    assert len(b1) == 1
    assert b1[nan] == 'a'
    # NaN as value: b['x'] = nan again must not raise
    b2 = bi_t()
    b2['x'] = nan
    b2['x'] = nan
    assert len(b2) == 1
    assert b2['x'] is nan
    # A key or value that duplicates an existing item's key and an existing
    # *different* item's value must still raise, even when it's the same NaN object:
    b3 = bi_t()
    b3[nan] = 'a'
    b3['x'] = nan
    with pytest.raises(KeyAndValueDuplicationError):
        b3[nan] = nan


def _skip_unless_dict_compares_stored_eq_lookup() -> None:
    probe: dict[t.Any, str] = {AsymStored(): 'hit'}
    if probe.get(AsymLookup()) != 'hit':
        pytest.skip('dict lookup on this runtime does not compare stored == lookup')


@pytest.mark.parametrize('bi_t', mutable_bidict_types)
def test_setitem_existing_is_noop_with_asymmetric_eq(bi_t: MBT[t.Any, t.Any]) -> None:
    """Setting an existing (key, val) pair should be a no-op even when __eq__ is asymmetric.

    dict lookup compares stored == lookup, so a lookup key that a stored key compares equal to
    hits the stored key's item even when lookup == stored is False.

    _dedup must agree with the dict lookups rather than re-checking equality itself
    (with operands in the opposite order) and wrongly concluding the items differ.
    See #382.
    """
    _skip_unless_dict_compares_stored_eq_lookup()
    stored, lookup = AsymStored(), AsymLookup()
    # Asymmetric key: dict considers *lookup* the same key as *stored* -> no-op
    b1 = bi_t()
    b1[stored] = 'v'
    b1[lookup] = 'v'
    assert len(b1) == 1
    assert next(iter(b1)) is stored
    # Asymmetric value -> no-op
    b2 = bi_t()
    b2['x'] = stored
    b2['x'] = lookup
    assert len(b2) == 1
    assert b2['x'] is stored


@pytest.mark.parametrize('bi_t', mutable_bidict_types)
@pytest.mark.parametrize('use_inv', [False, True], ids=['fwd', 'inv'])
@pytest.mark.parametrize('replace', ['value', 'key'])
@pytest.mark.parametrize('free_slot', [False, True], ids=['no-free-slot', 'free-slot'])
@pytest.mark.parametrize('fail', [False, True], ids=['write', 'rollback'])
def test_replacing_with_asymmetric_equal_object(
    bi_t: MBT[t.Any, t.Any], use_inv: bool, replace: str, free_slot: bool, fail: bool
) -> None:
    """Replacing a contained object with an asymmetrically equal one keeps a bidict and its inverse in sync.

    The contained *lookup* is replaced with *stored* (stored == lookup, but not lookup == stored), and the write
    either succeeds or is rolled back because the rest of the update fails. A dict lookup compares
    stored == lookup, so while both are in a backing mapping, operating on *lookup* can land on *stored*'s entry.
    *lookup*, *stored*, and 1 all hash to 1, so with *free_slot*, deleting the item containing 1 lets *stored*
    take the slot ahead of *lookup*'s; otherwise *stored* goes after it.
    """
    _skip_unless_dict_compares_stored_eq_lookup()
    stored, lookup = AsymStored(), AsymLookup()
    bi = bi_t()
    b = bi.inverse if use_inv else bi
    if replace == 'value':
        b.putall({'x': 1, 'k': lookup})
        if free_slot:
            del b['x']
        write = ('k', stored)
    else:
        b.putall({1: 'x', lookup: 'v'})
        if free_slot:
            del b[1]
        write = (stored, 'v')
    before = list(b.items())
    if fail:
        with pytest.raises(TypeError):
            b.forceupdate([write, (['unhashable'], 0)])
        after = list(b.items())
        if not isinstance(b, OrderedBidictBase):  # rolling back may reorder a non-ordered bidict's items
            before.sort(key=repr)
            after.sort(key=repr)
        assert len(after) == len(before)
        assert all(k1 is k2 and v1 is v2 for ((k1, v1), (k2, v2)) in zip(after, before, strict=True))
    else:
        b.forceput(*write)
        if replace == 'value':
            assert b['k'] is stored
        else:
            assert b.inverse['v'] is stored
            assert any(k is stored for k in b)
        assert len(b) == len(before)
    assert len(b.inverse) == len(b)
    assert all(b.inverse[v] is k for (k, v) in b.items())
    assert all(b[k] is v for (v, k) in b.inverse.items())


@pytest.mark.parametrize('bi_t', mutable_bidict_types)
@pytest.mark.parametrize('use_inv', [False, True], ids=['fwd', 'inv'])
@pytest.mark.parametrize('keep', ['key', 'value'])
def test_rolling_back_write_that_keeps_asymmetric_equal_object(
    bi_t: MBT[t.Any, t.Any], use_inv: bool, keep: str
) -> None:
    """Rolling back a write that keeps a contained object leaves another asymmetrically equal one in place.

    *lookup* and *stored* (stored == lookup, but not lookup == stored) are both contained, *lookup* first,
    so it takes the first slot for their shared hash. The write keeps *lookup* and replaces the other half
    of its item; then the update fails. While *lookup* is absent from a dict that holds *stored*, re-adding it
    lands on *stored*'s entry, so the rollback must not remove and re-add *lookup* in any backing dict,
    including an ordered bidict's node map (keyed by the keys, or through .inverse, by the values).
    """
    _skip_unless_dict_compares_stored_eq_lookup()
    stored, lookup = AsymStored(), AsymLookup()
    bi = bi_t()
    b = bi.inverse if use_inv else bi
    if keep == 'key':
        b.putall([(lookup, 'a'), (stored, 'b')])
        write = (lookup, 'c')
    else:
        b.putall([('a', lookup), ('b', stored)])
        write = ('c', lookup)
    before = list(b.items())
    with pytest.raises(TypeError):
        b.forceupdate([write, (['unhashable'], 0)])
    after = list(b.items())
    if not isinstance(b, OrderedBidictBase):  # rolling back may reorder a non-ordered bidict's items
        before.sort(key=repr)
        after.sort(key=repr)
    assert len(after) == len(before)
    assert all(k1 is k2 and v1 is v2 for ((k1, v1), (k2, v2)) in zip(after, before, strict=True))
    assert len(b.inverse) == len(b)
    assert all(b.inverse[v] is k for (k, v) in b.items())


def assert_calls_match(call1: Callable[..., t.Any], call2: Callable[..., t.Any]) -> None:
    results: dict[t.Any, t.Any] = {call1: None, call2: None}
    for call in results:
        try:
            results[call] = call()
        except Exception as exc:  # ruff: ignore[blind-except]
            results[call] = exc.__class__
    assert results[call1] == results[call2]


def assert_mappings_are_inverse(m1: Mapping[KT, VT], m2: Mapping[VT, KT]) -> None:
    assert len(m1) == len(m2)
    assert all(k == m2[v] for (k, v) in m1.items())
    assert m1.keys() == frozenset(m2.values())
    assert frozenset(m1.values()) == m2.keys()


def assert_bi_and_inv_are_inverse(bi: BB[KT, VT]) -> None:
    assert_mappings_are_inverse(bi, bi.inv)
    assert bi is bi.inv.inv
    assert bi.inv is bi.inv.inv.inv


def assert_orderedbidict_nodes_consistent(ob: OrderedBidictBase[KT, VT]) -> None:
    """The nodes in an ordered bidict's backing linked list should be the same as those in its backing mapping,
    which should map exactly the contained keys (or values, for an inverse) to them, so removed items aren't leaked.
    """
    assert set(ob._node_by_korv.inverse) == set(ob._sntl.iternodes())
    assert set(ob._node_by_korv) == set(ob if ob._bykey else ob.values())
    assert len(ob._node_by_korv) == len(ob)


def assert_bidicts_equal(b1: BB[KT, VT], b2: BB[KT, VT]) -> None:
    assert b1 == b2
    assert b1.inv == b2.inv
    assert_mappings_are_inverse(b1, b2.inv)
    assert_mappings_are_inverse(b1.inv, b2)

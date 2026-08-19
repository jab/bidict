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
import pickle
import sys
import typing as t
import weakref
from collections import UserDict
from collections.abc import Callable
from collections.abc import Mapping
from collections.abc import Reversible
from collections.abc import Sequence
from copy import copy
from copy import deepcopy
from functools import partial
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
from bidict_test_fixtures import Oracle
from bidict_test_fixtures import SupportsKeysAndGetItem
from bidict_test_fixtures import UserBi
from bidict_test_fixtures import UserBiBackedByDictSub
from bidict_test_fixtures import UserBiNotOwnInv
from bidict_test_fixtures import UserOrderedBi
from bidict_test_fixtures import UserOrderedBiBase
from bidict_test_fixtures import bidict_types
from bidict_test_fixtures import bomb
from bidict_test_fixtures import dedup
from bidict_test_fixtures import mutable_bidict_types
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

from bidict import BidictKeysView
from bidict import BidirectionalMapping
from bidict import DuplicationError
from bidict import KeyAndValueDuplicationError
from bidict import MutableBidict
from bidict import MutableBidirectionalMapping
from bidict import OnDup
from bidict import OnDupAction
from bidict import OrderedBidict
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

    @rule()
    def copy(self) -> None:
        for cp in (copy(self.bi), deepcopy(self.bi)):
            assert_bi_and_inv_are_inverse(cp)
            assert_bidicts_equal(cp, self.bi)

    @rule()
    def pickle(self) -> None:
        for b in (self.bi, self.bi.inv):
            roundtripped = pickle.loads(pickle.dumps(b))
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
        assert_update_fails_clean(self.bi, iter([*new, (bomb, 0)]), RuntimeError, on_dup)

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
        assert_update_fails_clean(self.bi, arg, (RuntimeError, DuplicationError), on_dup)

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
            assert check not in bi.items()
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
        it: t.Any = reversed if last else iter
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


# These test cases ensure coverage of all branches in [Ordered]BidictBase._undo_write.
# (Hypothesis doesn't always generate examples that cover all the branches otherwise.)
@pytest.mark.parametrize(('bi_t', 'on_dup'), list(product(mutable_bidict_types, on_dups)))
def test_putall_matches_bulk_put(bi_t: type[MutableBidict[int, int]], on_dup: OnDup) -> None:
    bi = bi_t({0: 0, 1: 1})
    for k1, v1, k2, v2 in product(range(4), repeat=4):
        for b in bi, bi.inv:
            assert_putall_matches_bulk_put(b, [(k1, v1), (k2, v2)], on_dup)


def assert_putall_matches_bulk_put(bi: MutableBidict[int, int], new_items: Items, on_dup: OnDup) -> None:
    tmp = bi.copy()
    checkexc = None
    expectexc = None
    try:
        for key, val in new_items:
            tmp.put(key, val, on_dup)
    except DuplicationError as exc:
        expectexc = type(exc)
        tmp = bi  # Since bulk updates fail clean, expect no changes (i.e. revert to bi).
    try:
        bi.putall(new_items, on_dup)
    except DuplicationError as exc:
        checkexc = type(exc)
    assert checkexc == expectexc
    assert bi == tmp
    assert bi.inv == tmp.inv


def assert_update_fails_clean(
    bi: MutableBidict[t.Any, t.Any],
    updates: t.Any,
    exc_t: type[Exception] | tuple[type[Exception], ...],
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
    # Keep self at least as large as updates so this sized arg takes the
    # in-place rollback path rather than the copy fast path.
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


def test_pickle_orderedbi_whose_order_disagrees_with_fwdm() -> None:
    """An OrderedBidict whose order does not match its _fwdm's should pickle with the correct order."""
    ob = OrderedBidict({0: 1, 2: 3})
    # First get ob._fwdm's order to disagree with ob's:
    ob.inv[1] = 4
    assert list(ob.items()) == [(4, 1), (2, 3)]
    assert list(ob._fwdm.items()) == [(2, 3), (4, 1)]
    # Now check that its order is preserved after pickling and unpickling:
    roundtripped = pickle.loads(pickle.dumps(ob))
    assert list(roundtripped.items()) == [(4, 1), (2, 3)]
    assert roundtripped.equals_order_sensitive(ob)


def test_pickle_dynamically_generated_inverse_bidict() -> None:
    """Instances of dynamically-generated inverse bidict classes should be pickleable."""
    ub: MutableBidict[str, int] = UserBiNotOwnInv(one=1, two=2)
    roundtripped = pickle.loads(pickle.dumps(ub))
    assert roundtripped == ub == UserBiNotOwnInv({'one': 1, 'two': 2})
    assert dict(roundtripped) == dict(ub)
    # Now for the inverse:
    assert repr(ub.inverse) == "UserBiNotOwnInvInv({1: 'one', 2: 'two'})"
    # We can still pickle the inverse, even though its class, _UserBidictInv, was
    # dynamically generated, and we didn't save a reference to it named "_UserBidictInv"
    # anywhere that pickle could find it in sys.modules:
    ubinv = pickle.loads(pickle.dumps(ub.inverse))
    assert repr(ubinv) == "UserBiNotOwnInvInv({1: 'one', 2: 'two'})"
    assert ub._inv_cls.__name__ not in (name for m in sys.modules for name in dir(m))


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
        bi.inverse  # noqa: B018


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
        weak = weakref.ref(bi)
        assert weak() is not None
        del bi
        assert weak() is None
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


@given(items121=items121)
def test_orderedbidict_nodes_consistent(items121: Items121) -> None:
    """The nodes in an ordered bidict's backing linked list should be the same as those in its backing mapping."""
    ob = OrderedBidict(items121)
    mapnodes = set(ob._node_by_korv.inverse)
    linkedlistnodes = set(ob._sntl.iternodes())
    assert mapnodes == linkedlistnodes


def test_dict_subclass_backing_gets_native_views() -> None:
    """A backing mapping that is a dict subclass should get the same views a dict would.

    keys()/items() dispatch on isinstance(fwdm, dict) rather than `fwdm_cls is dict`, so a
    dict subclass -- which is what every backing in the docs' recipes actually is, e.g.
    sortedcontainers.SortedDict -- gets its own native views. Those are reversible, carry a
    .mapping attribute, and implement their set operations in C, none of which a generic
    view over the bidict provides.
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

    for bi_t in (CustomReversed, SubCustom):
        assert issubclass(bi_t, Reversible)
        assert list(reversed(bi_t())) == ['custom'], bi_t


def test_set_reversed_is_idempotent() -> None:
    """Running _set_reversed() again must not make a computed __reversed__ look user-provided.

    It only runs once per class today, but were a repeat ever to mark the class as having a
    user-provided __reversed__, subclasses would inherit that and stop computing their own,
    which is exactly the bug that test_subclass_can_regain_reversibility covers.
    """

    class Computed(bidict[t.Any, t.Any]):
        pass

    Computed._set_reversed()
    assert not Computed._reversed_is_user_provided

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


#: Ways to mutate an ordered bidict, keyed by name. Each takes the bidict and the key
#: just yielded by the iteration in progress.
_MUTATIONS_DURING_ITERATION: t.Any = {
    'insert': lambda ob, key: ob.__setitem__(f'new{key}', f'new{key}'),
    'delete': lambda ob, key: ob.pop(next(k for k in ob if k != key), None),
    'clear': lambda ob, _key: ob.clear(),
    'move_to_end': lambda ob, key: ob.move_to_end(key),
    'collapse_to_fewer_items': lambda ob, key: ob.forceput(key, next(iter(ob.inv))),
    'insert_via_the_inverse': lambda ob, key: ob.inv.__setitem__(f'new{key}', f'new{key}'),
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
    Note the last mutation goes through the inverse, which shares the linked list, so it must
    invalidate this iterator too.
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


def test_orderedbidict_iteration_allows_value_only_update() -> None:
    """Updating an existing key's value does not restructure the list, so it must not raise.

    dict and OrderedDict both permit this, and an ordered bidict's iteration order is
    unaffected by it: the item keeps its node, and so its position.
    """
    ob = OrderedBidict({1: 'one', 2: 'two'})
    for key in ob:
        ob[key] = f'updated{key}'
    assert list(ob.items()) == [(1, 'updated1'), (2, 'updated2')]


def test_orderedbidict_iterator_created_before_mutation_raises() -> None:
    """The check must catch a mutation made after the iterator was created but before it ran.

    OrderedDict does this too, which is why iternodes() captures the version eagerly rather
    than on the first next() call.
    """
    ob = OrderedBidict({1: 'one', 2: 'two'})
    it = iter(ob)
    ob[3] = 'three'
    with pytest.raises(RuntimeError):
        list(it)


def test_orderedbidict_iteration_unaffected_by_unrelated_bidict() -> None:
    """Only mutations to *this* bidict's linked list invalidate its iterators."""
    ob, other = OrderedBidict({1: 'one', 2: 'two'}), OrderedBidict({3: 'three'})
    keys = []
    for key in ob:
        other[key] = f'x{key}'  # a different bidict, so a different linked list
        keys.append(key)
    assert keys == [1, 2]


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

    Regression test: the set-operation proxy methods in _OrderedBidictKeysView and
    _OrderedBidictItemsView previously passed the opposing custom view type directly to the
    C-level dict_keys/dict_items methods, which returned NotImplemented (they only recognize
    dict_keys and dict_items). With both sides returning NotImplemented, Python raised TypeError
    (for the ordering comparisons) or fell back to the wrong answer (e.g. identity-based __eq__).
    The fix extracts the backing dict view from a cross-type _OView arg before forwarding.
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


def test_abc_slots() -> None:
    """Bidict ABCs should define __slots__.

    Ref: https://docs.python.org/3/reference/datamodel.html#notes-on-using-slots

    Note: non-abstract bidict types do not define __slots__ as of v0.22.0.
    """
    assert BidirectionalMapping.__dict__['__slots__'] == ()
    assert MutableBidirectionalMapping.__dict__['__slots__'] == ()


@pytest.mark.parametrize('bi_t', bidict_types)
def test_values_view_reversibility_matches_bidict(bi_t: BT[t.Any, t.Any]) -> None:
    """values() iterates the backing forward mapping, so it must be reversible
    exactly when the bidict itself is -- never advertising a reversed() that raises.
    """
    bi = bi_t({1: -1, 2: -2})
    values = bi.values()
    if isinstance(bi, Reversible):
        assert isinstance(values, Reversible)
        assert list(reversed(values)) == list(bi.values())[::-1]
    else:
        assert not isinstance(values, Reversible)
        with pytest.raises(TypeError):  # and the claim is not a lie
            reversed(t.cast(t.Any, values))


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


class _AsymStored:
    """Pathological type equal to _AsymLookup instances, but only when on the left-hand side."""

    @override
    def __hash__(self) -> int:
        return 1

    @override
    def __eq__(self, other: object) -> bool:
        return isinstance(other, _AsymLookup)


class _AsymLookup:
    """Pathological type that is never equal to anything, even when an _AsymStored equals it."""

    @override
    def __hash__(self) -> int:
        return 1

    @override
    def __eq__(self, other: object) -> bool:
        return False


@pytest.mark.parametrize('bi_t', mutable_bidict_types)
def test_setitem_existing_is_noop_with_asymmetric_eq(bi_t: MBT[t.Any, t.Any]) -> None:
    """Setting an existing (key, val) pair should be a no-op even when __eq__ is asymmetric.

    dict lookup compares stored == lookup, so a lookup key that a stored key compares equal to
    hits the stored key's item even when lookup == stored is False.

    _dedup must agree with the dict lookups rather than re-checking equality itself
    (with operands in the opposite order) and wrongly concluding the items differ.
    See #382.
    """
    stored, lookup = _AsymStored(), _AsymLookup()
    probe: dict[t.Any, str] = {stored: 'hit'}
    if probe.get(lookup) != 'hit':
        pytest.skip('dict lookup on this runtime does not compare stored == lookup')
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


def assert_calls_match(call1: Callable[..., t.Any], call2: Callable[..., t.Any]) -> None:
    results: dict[t.Any, t.Any] = {call1: None, call2: None}
    for call in results:
        try:
            results[call] = call()
        except Exception as exc:  # noqa: BLE001
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


def assert_bidicts_equal(b1: BB[KT, VT], b2: BB[KT, VT]) -> None:
    assert b1 == b2
    assert b1.inv == b2.inv
    assert_mappings_are_inverse(b1, b2.inv)
    assert_mappings_are_inverse(b1.inv, b2)

# Copyright 2009-2024 Joshua Bronson. All rights reserved.
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
from copy import copy
from copy import deepcopy
from functools import partial
from itertools import product
from itertools import starmap
from random import Random
from unittest.mock import ANY

import pytest
from bidict_test_fixtures import BB
from bidict_test_fixtures import BT
from bidict_test_fixtures import KT
from bidict_test_fixtures import MBT
from bidict_test_fixtures import SET_OPS
from bidict_test_fixtures import VT
from bidict_test_fixtures import Oracle
from bidict_test_fixtures import SupportsKeysAndGetItem
from bidict_test_fixtures import UserBiNotOwnInv
from bidict_test_fixtures import UserOrderedBi
from bidict_test_fixtures import bidict_types
from bidict_test_fixtures import dedup
from bidict_test_fixtures import mutable_bidict_types
from bidict_test_fixtures import should_be_reversible
from bidict_test_fixtures import update_arg_types
from bidict_test_fixtures import zip_equal
from hypothesis import assume
from hypothesis import given
from hypothesis import note
from hypothesis.stateful import RuleBasedStateMachine
from hypothesis.stateful import initialize
from hypothesis.stateful import invariant
from hypothesis.stateful import precondition
from hypothesis.stateful import rule
from hypothesis.strategies import booleans
from hypothesis.strategies import dictionaries
from hypothesis.strategies import frozensets
from hypothesis.strategies import integers
from hypothesis.strategies import lists
from hypothesis.strategies import randoms
from hypothesis.strategies import sampled_from
from hypothesis.strategies import tuples

from bidict import BidirectionalMapping
from bidict import DuplicationError
from bidict import KeyAndValueDuplicationError
from bidict import MutableBidict
from bidict import MutableBidirectionalMapping
from bidict import OnDup
from bidict import OnDupAction
from bidict import OrderedBidict
from bidict import ValueDuplicationError
from bidict import frozenbidict
from bidict import inverted
from bidict._typing import MapOrItems


MAX_SIZE = 5  # Used for init_items and updates. 5 is enough to cover all possible duplication scenarios.


keys = integers(min_value=1, max_value=10)
vals = keys.map(operator.neg)
InitItems: t.TypeAlias = t.Dict[t.Any, t.Any]
init_items = dictionaries(vals, keys, max_size=MAX_SIZE).map(lambda d: {v: k for (k, v) in d.items()})  # no dup vals
bidict_t = sampled_from(bidict_types)
mut_bidict_t = sampled_from(mutable_bidict_types)
items = tuples(keys, vals)
ItemLists: t.TypeAlias = t.List[t.Tuple[int, int]]
itemlists = lists(items, max_size=MAX_SIZE)  # "lists" to allow testing updates with dup k and/or v
updates_t = sampled_from(update_arg_types)
itemsets = frozensets(items, max_size=MAX_SIZE)
on_dups = tuple(starmap(OnDup, product(OnDupAction, repeat=2)))
on_dup = sampled_from(on_dups)


class BidictStateMachine(RuleBasedStateMachine):
    bi: MutableBidict[int, int]
    oracle: Oracle[int, int]

    @initialize(mut_bidict_t=mut_bidict_t, init_items=init_items)
    def init(self, mut_bidict_t: type[MutableBidict[int, int]], init_items: InitItems) -> None:
        self.bi = mut_bidict_t(init_items)
        self.oracle = Oracle(init_items, ordered=self.is_ordered())

    def is_ordered(self) -> bool:
        return isinstance(self.bi, OrderedBidict)

    @invariant()
    def assert_match_oracle(self) -> None:
        note(f'> {self.bi=}\n> {self.oracle.data=}')
        self.oracle.assert_match(self.bi)

    viewnames = sampled_from(('keys', 'values', 'items'))

    # Would make this an invariant rather than a rule, but it slows down the tests too much.
    @rule(rand=randoms(), viewname=viewnames, set_op=sampled_from(SET_OPS), other_set=itemsets)
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

    @precondition(lambda self: should_be_reversible(self.bi.__class__))
    @invariant()
    def assert_reversed_works(self) -> None:
        assert list(reversed(self.bi)) == list(self.bi)[::-1]
        assert list(reversed(self.bi.items())) == list(self.bi.items())[::-1]
        if self.is_ordered():
            assert zip_equal(reversed(self.bi), reversed(self.oracle.data))
            assert zip_equal(reversed(self.bi.items()), reversed(self.oracle.data.items()))
            assert zip_equal(reversed(self.bi.values()), reversed(self.oracle.data.values()))

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
    def put(self, key: int, val: complex, on_dup: OnDup) -> None:
        assert_calls_match(
            partial(self.bi.put, key, val, on_dup),
            partial(self.oracle.put, key, val, on_dup),
        )

    @rule(updates=itemlists, updates_t=updates_t, on_dup=on_dup)
    def putall(self, updates: MapOrItems[int, int], updates_t: t.Any, on_dup: OnDup) -> None:
        # Don't let the updates_t(updates) calls below raise a DuplicationError.
        if isinstance(updates_t, type) and issubclass(updates_t, BidirectionalMapping):
            updates = dedup(updates)
        # Since updates_t can be iter, can't extract the two updates_t(updates) calls below into a single value.
        assert_calls_match(
            partial(self.bi.putall, updates_t(updates), on_dup),
            partial(self.oracle.putall, updates_t(updates), on_dup),
        )

    @rule(other=init_items)
    def __ior__(self, other: t.Mapping[KT, VT]) -> None:
        assert_calls_match(
            partial(self.bi.__ior__, other),
            partial(self.oracle.__ior__, other),
        )

    @rule(other=init_items)
    def __or__(self, other: t.Mapping[KT, VT]) -> None:
        assert_calls_match(
            partial(self.bi.__or__, other),
            partial(self.oracle.__or__, other),
        )

    # https://bidict.rtfd.io/basic-usage.html#order-matters
    @precondition(lambda self: zip_equal(self.bi, self.oracle.data))
    @rule(other=init_items)
    def __ror__(self, other: t.Mapping[KT, VT]) -> None:
        assert_calls_match(
            partial(self.bi.__ror__, other),
            partial(self.oracle.__ror__, other),
        )

    @precondition(lambda self: len(self.bi) >= 2)
    @rule(random=randoms())
    def update_with_dup(self, random: Random) -> None:
        # Covered nondeterministically by the more general "putall" rule above, but this ensures that basic duplication
        # scenarios are deterministically covered.
        len_before = len(self.bi)
        # Choose two existing items at random.
        (k1, v1), (k2, v2) = random.sample(tuple(self.oracle.data.items()), 2)
        # Inserting (new_key, dup_val) should raise ValueDuplicationError.
        with pytest.raises(ValueDuplicationError):
            self.bi.update([('foo', 'foo'), ('bar', v1)])  # type: ignore[list-item]
        # Any partial update applied before the failure should have been rolled back (fails clean).
        assert len(self.bi) == len_before
        assert 'foo' not in self.bi  # type: ignore[comparison-overlap]
        assert self.bi.inv[v1] != 'bar'  # type: ignore[comparison-overlap]
        # key and value duplication across two different items should raise KeyAndValueDuplicationError.
        for key, val in ((k1, v2), (k2, v1)):
            with pytest.raises(KeyAndValueDuplicationError):
                self.bi.update([('foo', 'foo'), (key, val)])  # type: ignore[list-item]
            assert len(self.bi) == len_before
            assert 'foo' not in self.bi  # type: ignore[comparison-overlap]
            assert self.bi[key] != val
        # Inserting already-present items should be a no-op.
        self.bi.update([(k1, v1), (k2, v2)])
        assert len(self.bi) == len_before

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
    @rule(last=booleans())
    def popitem(self, last: bool) -> None:
        kw = {'last': last} if self.is_ordered() else {}
        popped_item = self.bi.popitem(**kw)
        self.oracle.pop(popped_item[0])
        assert popped_item not in self.bi.items()
        if self.is_nonempty():
            inv_popped_item = self.bi.inv.popitem(**kw)
            self.oracle.pop(inv_popped_item[1])
            assert inv_popped_item not in self.bi.inv.items()

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
        key, val = random.choice(tuple(self.oracle.data.items()))
        self.bi.move_to_end(key, last=last)  # type: ignore[attr-defined]
        self.oracle.move_to_end(key, last=last)
        it: t.Any = reversed if last else iter
        assert (key, val) == next(it(self.bi.items()))
        assert (val, key) == next(it(self.bi.inv.items()))
        assert (key, val) == next(it(self.oracle.data.items()))
        assert (val, key) == next(it(self.oracle.data_inv.items()))


BidictStateMachineTest = BidictStateMachine.TestCase


@pytest.mark.parametrize('bi_t', bidict_types)
def test_init_and_update_with_bad_args(bi_t: BT[KT, VT]) -> None:
    for bad_args in ((None,), (0,), (False,), (True,), ({}, {})):  # type: ignore[var-annotated]
        with pytest.raises(TypeError):
            bi_t(*bad_args)  # type: ignore[arg-type]
        if not issubclass(bi_t, MutableBidict):
            continue
        bi = bi_t()
        with pytest.raises(TypeError):
            bi.update(*bad_args)  # type: ignore[arg-type]


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
        bi.move_to_end('foo')  # type: ignore[arg-type]


@pytest.mark.parametrize('bi_t', bidict_types)
def test_eq_defers_to_other_eq(bi_t: BT[KT, VT]) -> None:
    """bidict.__eq__(other) should defer to other.__eq__ when other is not a mapping."""
    # ANY.__eq__ always returns true, so this test will fail if bi_t.__eq__ fails to defer.
    assert bi_t() == ANY


@pytest.mark.parametrize(('bi_t', 'non_mapping'), product(bidict_types, (None, 1, [], SupportsKeysAndGetItem({}))))
def test_eq_and_or_with_non_mapping(bi_t: BT[KT, VT], non_mapping: t.Any) -> None:
    bi = bi_t()
    assert bi != non_mapping
    assert not bi.equals_order_sensitive(non_mapping)
    with pytest.raises(TypeError):
        bi | non_mapping
    with pytest.raises(TypeError):
        non_mapping | bi


@given(init_items=init_items, bidict_t=bidict_t, rand=randoms())
def test_ne_ordsens_to_equal_map_with_diff_order(init_items: InitItems, bidict_t: BT[KT, VT], rand: Random) -> None:
    bi = bidict_t(init_items)
    items_shuf = list(init_items.items())
    rand.shuffle(items_shuf)
    assume(not zip_equal(items_shuf, init_items.items()))
    map_shuf = dict(items_shuf)
    assert bi == map_shuf
    assert not bi.equals_order_sensitive(map_shuf)


@given(items=itemlists, bidict_t=bidict_t)
def test_inverted(items: ItemLists, bidict_t: BT[int, int]) -> None:
    check_list = list(inverted(inverted(items)))
    expect_list = items
    assert check_list == expect_list
    items_nodup = dedup(items)
    check_bi = bidict_t(inverted(bidict_t(items_nodup)))
    expect_bi = bidict_t({v: k for (k, v) in items_nodup.items()})
    assert_bidicts_equal(check_bi, expect_bi)


@given(init_items=init_items)
def test_frozenbidicts_hashable(init_items: InitItems) -> None:
    """Frozen bidicts can be hashed (and therefore inserted into sets and mappings)."""
    from hypothesis import event

    event('size', len(init_items))
    bi = frozenbidict(init_items)
    h1 = hash(bi)
    h2 = hash(bi)
    assert h1 == h2
    assert {bi}
    assert {bi: bi}
    bi2 = frozenbidict(init_items)
    assert bi2 == bi
    assert hash(bi2) == h1


# These test cases ensure coverage of all branches in [Ordered]BidictBase._undo_write.
# (Hypothesis doesn't always generate examples that cover all the branches otherwise.)
@pytest.mark.parametrize(('bi_t', 'on_dup'), product(mutable_bidict_types, on_dups))
def test_putall_matches_bulk_put(bi_t: type[MutableBidict[int, int]], on_dup: OnDup) -> None:
    init_items = {0: 0, 1: 1}
    bi = bi_t(init_items)
    for k1, v1, k2, v2 in product(range(4), repeat=4):
        for b in bi, bi.inv:
            assert_putall_matches_bulk_put(b, [(k1, v1), (k2, v2)], on_dup)


def assert_putall_matches_bulk_put(bi: MutableBidict[int, int], new_items: ItemLists, on_dup: OnDup) -> None:
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
        __getitem__ = __iter__ = __len__ = ...  # type: ignore [assignment]

        @property
        def inverse(self) -> t.Any:
            return super().inverse  # type: ignore [safe-super]

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
@given(init_items=init_items)
def test_orderedbidict_nodes_freed_on_zero_refcount(init_items: InitItems) -> None:
    """On CPython, the moment you have no more references to an ordered bidict,
    the refcount of each of its internal nodes drops to 0
    (i.e. the linked list of nodes does not create a reference cycle),
    allowing the memory to be reclaimed immediately.
    """
    gc.disable()
    try:
        ob = OrderedBidict(init_items)
        nodes = weakref.WeakSet(ob._sntl.iternodes())
        assert len(nodes) == len(ob)
        del ob
        assert len(nodes) == 0
    finally:
        gc.enable()


@given(init_items=init_items)
def test_orderedbidict_nodes_consistent(init_items: InitItems) -> None:
    """The nodes in an ordered bidict's backing linked list should be the same as those in its backing mapping."""
    ob = OrderedBidict(init_items)
    mapnodes = set(ob._node_by_korv.inverse)
    linkedlistnodes = set(ob._sntl.iternodes())
    assert mapnodes == linkedlistnodes


def test_abc_slots() -> None:
    """Bidict ABCs should define __slots__.

    Ref: https://docs.python.org/3/reference/datamodel.html#notes-on-using-slots

    Note: non-abstract bidict types do not define __slots__ as of v0.22.0.
    """
    assert BidirectionalMapping.__dict__['__slots__'] == ()
    assert MutableBidirectionalMapping.__dict__['__slots__'] == ()


@pytest.mark.parametrize('bi_t', bidict_types)
def test_inv_aliases_inverse(bi_t: BT[KT, VT]) -> None:
    """bi.inv should alias bi.inverse."""
    bi = bi_t()
    assert bi.inverse is bi.inv
    assert bi.inv.inverse is bi.inverse.inv


def assert_calls_match(call1: t.Callable[..., t.Any], call2: t.Callable[..., t.Any]) -> None:
    results: dict[t.Any, t.Any] = {call1: None, call2: None}
    for call in results:
        try:
            results[call] = call()
        except Exception as exc:  # noqa: BLE001, PERF203
            results[call] = exc.__class__
    assert results[call1] == results[call2]


def assert_mappings_are_inverse(m1: t.Mapping[KT, VT], m2: t.Mapping[VT, KT]) -> None:
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

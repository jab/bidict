# Copyright 2009-2023 Joshua Bronson. All rights reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Property-based tests using https://hypothesis.readthedocs.io."""

from __future__ import annotations
from copy import deepcopy
from collections import OrderedDict, UserDict
from collections.abc import Iterable, KeysView, ValuesView, ItemsView
from itertools import tee
from unittest.mock import ANY
import gc
import operator as op
import pickle
import sys
import typing as t
import weakref

import pytest
from hypothesis import assume, example, given

from bidict import (
    DROP_NEW, DROP_OLD, RAISE, OnDup,
    BidirectionalMapping, MutableBidirectionalMapping, BidictBase, MutableBidict, OrderedBidictBase,
    OrderedBidict, bidict, namedbidict,
    inverted,
    DuplicationError, KeyDuplicationError, ValueDuplicationError, KeyAndValueDuplicationError,
)
from bidict._iter import iteritems
from bidict._typing import Items, TypeAlias

from . import _strategies as st
from ._types import (
    ORDER_PRESERVING_BIDICT_TYPES,
    BIDICT_TYPE_WHOSE_MODULE_HAS_REF_TO_INV_CLS,
    BIDICT_TYPE_WHOSE_MODULE_HAS_NO_REF_TO_INV_CLS,
)


skip_if_pypy = pytest.mark.skipif(
    sys.implementation.name == 'pypy',
    reason='Requires CPython refcounting behavior',
)


Bi: TypeAlias = BidictBase[t.Any, t.Any]
MBi: TypeAlias = MutableBidict[t.Any, t.Any]
OBi: TypeAlias = OrderedBidictBase[t.Any, t.Any]


@given(st.BIDICTS, st.NON_MAPPINGS)
def test_unequal_to_non_mapping(bi: Bi, not_a_mapping: t.Any) -> None:
    """Bidicts and their inverses should compare unequal to bools, ints, and other typical non-mappings."""
    assert bi != not_a_mapping
    assert bi.inv != not_a_mapping
    assert not bi == not_a_mapping
    assert not bi.inv == not_a_mapping


@given(st.BIDICTS)
def test_eq_correctly_defers_to_eq_of_non_mapping(bi: Bi) -> None:
    """Bidicts' __eq__ does not defeat non-mapping objects' __eq__, when implemented."""
    assert bi == ANY
    assert ANY == bi


@given(st.BI_AND_MAP_FROM_DIFF_ITEMS)
def test_unequal_to_mapping_with_different_items(bi_and_map_from_diff_items: t.Any) -> None:
    """Bidicts should be unequal to mappings containing different items."""
    bi, mapping = bi_and_map_from_diff_items
    assert bi != mapping
    assert not bi == mapping


@given(st.BI_AND_MAP_FROM_SAME_ND_ITEMS)
def test_equal_to_mapping_with_same_items(bi_and_map_from_same_items: t.Any) -> None:
    """Bidicts should be equal to mappings created from the same non-duplicating items.

    The bidict's inverse and the mapping's inverse should also be equal.
    """
    bi, mapping = bi_and_map_from_same_items
    assert bi == mapping
    assert mapping == bi
    assert not bi != mapping
    assert not mapping != bi
    mapping_inv = OrderedDict((v, k) for (k, v) in mapping.items())
    assert bi.inv == mapping_inv
    assert mapping_inv == bi.inv
    assert not bi.inv != mapping_inv
    assert not mapping_inv != bi.inv


@given(st.HBI_AND_HMAP_FROM_SAME_ND_ITEMS)
def test_equal_hashables_have_same_hash(hashable_bidict_and_mapping: t.Any) -> None:
    """Hashable bidicts and hashable mappings that are equal should hash to the same value."""
    bi, mapping = hashable_bidict_and_mapping
    assert bi == mapping
    assert mapping == bi
    assert hash(bi) == hash(mapping)


@given(st.BIDICTS, st.NON_BI_MAPPINGS)
@example(OrderedBidict([(1, 1), (2, 2)]), OrderedDict([(1, 1), (2, 2)]))
@example(OrderedBidict([(1, 1), (2, 2)]), OrderedDict([(2, 2), (1, 1)]))
@example(OrderedBidict({None: None}), {False: None, None: None})
def test_equals_matches_equals_order_sensitive(bi: Bi, mapping: t.Mapping[t.Any, t.Any]) -> None:
    """Bidict equals_order_sensitive should agree with __eq__."""
    mapping_inv = OrderedDict((v, k) for (k, v) in mapping.items())
    if bi.equals_order_sensitive(mapping):
        assert bi == mapping
        assert mapping == bi
        assert list(bi.inv.items()) == list(mapping_inv.items())
    else:
        assert list(bi.items()) != list(mapping.items())
        if bi == mapping:
            assert mapping == bi
            assert bi.items() == mapping.items()  # should use (unordered) set comparison
            assert bi.inv.items() == mapping_inv.items()  # ditto
            assert mapping_inv.items() == bi.inv.items()  # ditto
        else:
            assert mapping != bi
            assert bi.items() != mapping.items()
            assert bi.inv.items() != mapping_inv.items() or len(mapping_inv) != len(mapping)
            assert mapping_inv.items() != bi.inv.items() or len(mapping_inv) != len(mapping)


@given(st.BI_AND_MAP_FROM_SAME_ND_ITEMS)
def test_equals_order_sensitive_same_items(bi_and_map_from_same_items: t.Any) -> None:
    """Bidicts should be order-sensitive-equal to mappings with the same items in the same order.

    The bidict's inverse and the ordered mapping's inverse should also be order-sensitive-equal.
    """
    bi, mapping = bi_and_map_from_same_items
    assert bi.equals_order_sensitive(mapping)
    mapping_inv = OrderedDict((v, k) for (k, v) in mapping.items())
    assert bi.inv.equals_order_sensitive(mapping_inv)


@given(st.OBI_AND_OMAP_FROM_SAME_ITEMS_DIFF_ORDER)
def test_unequal_order_sensitive_same_items_different_order(ob_and_om: t.Any) -> None:
    """Ordered bidicts should be order-sensitive-unequal to ordered mappings of diff-ordered items.

    Where both were created from the same items where no key or value was duplicated,
    but the items were ordered differently.

    The bidict's inverse and the ordered mapping's inverse should also be order-sensitive-unequal.
    """
    ob, om = ob_and_om
    assert not ob.equals_order_sensitive(om)
    om_inv = OrderedDict((v, k) for (k, v) in om.items())
    assert not ob.inv.equals_order_sensitive(om_inv)


@given(st.ORDERED_BIDICTS, st.NON_MAPPINGS)
def test_unequal_order_sensitive_non_mapping(ob: OBi, not_a_mapping: t.Any) -> None:
    """Ordered bidicts should be order-sensitive-unequal to ordered mappings of diff-ordered items.

    Where both were created from the same items where no key or value was duplicated,
    but the items were ordered differently.

    The bidict's inverse and the ordered mapping's inverse should also be order-sensitive-unequal.
    """
    assert not ob.equals_order_sensitive(not_a_mapping)
    assert not ob.inv.equals_order_sensitive(not_a_mapping)


@given(st.BIDICTS, st.NON_BI_MAPPINGS)
def test_merge_operators(bi: Bi, mapping: t.Mapping[t.Any, t.Any]) -> None:
    """PEP 584-style dict merge operators should work as expected."""
    try:
        merged = bi | mapping
    except DuplicationError as exc:
        with pytest.raises(exc.__class__):
            bidict(bi).update(mapping)
        with pytest.raises(exc.__class__):
            bi |= mapping
    else:
        assert merged == bidict({**bi, **mapping})
        tmp = bidict(bi)
        tmp |= mapping  # type: ignore
        assert merged == tmp

    try:
        merged = mapping | bi
    except DuplicationError as exc:
        with pytest.raises(exc.__class__):
            bidict(mapping).update(bi)
    else:
        assert merged == bidict({**mapping, **bi})
        mapping |= bi
        assert merged == mapping


@given(st.MUTABLE_BIDICTS, st.DIFF_ATOMS, st.RANDOMS)
def test_setitem_with_dup_val_raises(bi: MBi, new_key: t.Any, rand: t.Any) -> None:
    """Setting an item whose value duplicates that of an existing item should raise ValueDuplicationError."""
    ln = len(bi)
    assume(ln > 2)
    for b in (bi, bi.inv):
        existing_val = rand.choice(list(b.inv))
        with pytest.raises(ValueDuplicationError):
            b[new_key] = existing_val  # type: ignore
        assert len(b) == len(b.inv) == ln


@given(st.MUTABLE_BIDICTS, st.RANDOMS)
def test_setitem_with_dup_key_val_raises(bi: MBi, rand: t.Any) -> None:
    """Setting an item whose key and val duplicate two different existing items raises KeyAndValueDuplicationError."""
    ln = len(bi)
    assume(ln > 2)
    for b in (bi, bi.inv):
        existing_items = rand.sample(list(b.items()), 2)
        existing_key = existing_items[0][0]
        existing_val = existing_items[1][1]
        with pytest.raises(KeyAndValueDuplicationError):
            b[existing_key] = existing_val  # type: ignore
        assert len(b) == len(b.inv) == ln


@given(st.MUTABLE_BIDICTS, st.DIFF_ATOMS, st.RANDOMS)
def test_put_with_dup_key_raises(bi: MBi, new_val: t.Any, rand: t.Any) -> None:
    """Putting an item whose key duplicates that of an existing item should raise KeyDuplicationError."""
    ln = len(bi)
    assume(ln > 2)
    for b in (bi, bi.inv):
        existing_key = rand.choice(list(b))
        with pytest.raises(KeyDuplicationError):
            b.put(existing_key, new_val)  # type: ignore
        assert len(b) == len(b.inv) == ln


@given(st.BIDICTS)
def test_bijectivity(bi: Bi) -> None:
    """b[k] == v  <==>  b.inv[v] == k"""
    for b in (bi, bi.inv):
        assert all(b.inv[v] == k for (k, v) in b.items())


@given(st.MUTABLE_BIDICTS)
def test_cleared_bidicts_have_no_items(bi: MBi) -> None:
    """A cleared bidict should contain no items."""
    bi.clear()
    assert not bi
    assert len(bi) == 0
    sntl = object()
    assert next(iter(bi), sntl) is sntl


@given(st.BI_AND_CMPDICT_FROM_SAME_ITEMS, st.DATA)
def test_consistency_after_method_call(bi_and_cmp_dict: t.Any, data: t.Any) -> None:
    """A bidict should be left in a consistent state after calling any method, even if it raises."""
    bi_orig, cmp_dict_orig = bi_and_cmp_dict
    for methodname, args_strat in st.METHOD_ARGS_PAIRS:
        if not hasattr(bi_orig, methodname):
            continue
        bi = bi_orig.copy()
        collect = list if isinstance(bi, ORDER_PRESERVING_BIDICT_TYPES) else set
        method = getattr(bi, methodname)
        args = data.draw(args_strat) if args_strat is not None else ()
        try:
            result = method(*args)
        except (KeyError, TypeError, DuplicationError) as exc:
            if isinstance(exc, TypeError):
                assert methodname == 'popitem', 'popitem should be the only method that can raise TypeError here (we sometimes pass in the wrong number of args)'
            # Call should fail clean, i.e. bi should be in the same state it was before the call.
            assertmsg = f'{method!r} did not fail clean: {exc!r}'
            assert bi == bi_orig, assertmsg
            assert bi.inv == bi_orig.inv, assertmsg
            assert collect(bi.keys()) == collect(bi_orig.keys()), assertmsg
            assert collect(bi.values()) == collect(bi_orig.values()), assertmsg
            assert collect(bi.items()) == collect(bi_orig.items()), assertmsg
            assert collect(reversed(bi.keys())) == collect(reversed(bi_orig.keys())), assertmsg
            assert collect(reversed(bi.values())) == collect(reversed(bi_orig.values())), assertmsg
            assert collect(reversed(bi.items())) == collect(reversed(bi_orig.items())), assertmsg
        else:
            # Should get the same result as calling the same method on the compare-to dict.
            cmp_dict = cmp_dict_orig.copy()
            cmp_dict_meth = getattr(cmp_dict, methodname, None)
            if cmp_dict_meth:
                cmp_result = cmp_dict_meth(*args)
                if isinstance(cmp_result, Iterable):
                    result = collect(result)
                    cmp_result = collect(cmp_result)
                assert result == cmp_result, f'methodname={methodname} args={args!r}'
        # Whether the call failed or succeeded, bi should pass consistency checks.
        keys = collect(bi.keys())
        assert keys == collect(bi)
        vals = collect(bi.values())
        assert vals == collect(bi[k] for k in bi)
        items = collect(bi.items())
        assert items == collect((k, bi[k]) for k in bi)
        assert collect(bi.inv.keys()) == collect(bi.inv) == vals
        assert collect(bi.inv.values()) == collect(bi.inv[k] for k in bi.inv) == keys
        assert collect(bi.inv.items()) == collect((k, bi.inv[k]) for k in bi.inv)
        if not getattr(bi.keys(), '__reversed__', None):  # Python < 3.8
            return
        assert collect(reversed(bi.keys())) == collect(reversed(bi.inv.values()))
        assert collect(reversed(bi.values())) == collect(reversed(bi.inv.keys()))
        assert collect(reversed(bi.items())) == collect((k, v) for (v, k) in reversed(bi.inv.items()))


@given(st.MUTABLE_BIDICTS, st.L_PAIRS, st.ON_DUP)
# These test cases ensure coverage of all branches in [Ordered]BidictBase._undo_write
# (Hypothesis doesn't always generate examples that cover all the branches otherwise).
@example(bidict({1: 1, 2: 2}), [(1, 3), (1, 2)], OnDup(DROP_OLD, RAISE))
@example(bidict({1: 1, 2: 2}), [(3, 1), (2, 4)], OnDup(RAISE, DROP_OLD))
@example(bidict({1: 1, 2: 2}), [(1, 2), (1, 1)], OnDup(RAISE, RAISE, DROP_OLD))
@example(OrderedBidict({1: 1, 2: 2}), [(1, 3), (1, 2)], OnDup(DROP_OLD, RAISE))
@example(OrderedBidict({1: 1, 2: 2}), [(3, 1), (2, 4)], OnDup(RAISE, DROP_OLD))
@example(OrderedBidict({1: 1, 2: 2}), [(1, 2), (1, 1)], OnDup(RAISE, RAISE, DROP_OLD))
@example(OrderedBidict(), [(1, 1), (2, 2), (1, 2), (1, 1), (2, 1)], OnDup(DROP_OLD, RAISE, DROP_OLD))
@example(OrderedBidict(), [(1, 2), (2, 1), (1, 1), (1, 2)], OnDup(RAISE, DROP_NEW, DROP_OLD))
@example(OrderedBidict(), [(1, 1), (2, 1), (1, 1)], OnDup(DROP_NEW, DROP_OLD, DROP_NEW))
def test_putall_same_as_put_for_each_item(bi: MBi, items: Items[t.Any, t.Any], on_dup: OnDup) -> None:
    """*bi.putall(items) <==> for i in items: bi.put(i)* for all values of OnDup."""
    check = bi.copy()
    expect = bi.copy()
    checkexc = None
    expectexc = None
    for (key, val) in items:
        try:
            expect.put(key, val, on_dup)
        except DuplicationError as exc:
            expectexc = type(exc)
            expect = bi  # Bulk updates fail clean -> roll back to original state.
            break
    try:
        check.putall(items, on_dup)
    except DuplicationError as exc:
        checkexc = type(exc)
    assert checkexc == expectexc
    assert check == expect
    assert check.inv == expect.inv


@given(st.BI_AND_MAP_FROM_SAME_ND_ITEMS)
def test_bidict_iter(bi_and_mapping: t.Any) -> None:
    """iter(bi) should yield the keys in a bidict in insertion order."""
    bi, mapping = bi_and_mapping
    assert all(i == j for (i, j) in zip(bi, mapping))


@given(st.RBI_AND_RMAP_FROM_SAME_ND_ITEMS)
def test_bidict_reversed(rb_and_rd: t.Any) -> None:
    """reversed(bi) should yield the keys in a bidict in reverse insertion order."""
    rb, rd = rb_and_rd
    assert all(i == j for (i, j) in zip(reversed(rb), reversed(rd)))


@given(st.FROZEN_BIDICTS)
def test_frozenbidicts_hashable(bi: Bi) -> None:
    """Frozen bidicts can be hashed and inserted into sets and mappings."""
    assert hash(bi)
    assert {bi}
    assert {bi: bi}


@given(st.NAMEDBIDICT_NAMES_SOME_INVALID)
def test_namedbidict_raises_on_invalid_name(names: tuple[str, str, str]) -> None:
    """:func:`bidict.namedbidict` should raise if given invalid names."""
    typename, keyname, valname = names
    with pytest.raises(ValueError):
        namedbidict(typename, keyname, valname)


@given(st.NAMEDBIDICT_NAMES_ALL_VALID)
def test_namedbidict_raises_on_same_keyname_as_valname(names: tuple[str, str, str]) -> None:
    """:func:`bidict.namedbidict` should raise if given same keyname as valname."""
    typename, keyname, _ = names
    with pytest.raises(ValueError):
        namedbidict(typename, keyname, keyname)


@given(st.NAMEDBIDICT_NAMES_ALL_VALID, st.NON_BI_MAPPING_TYPES)
def test_namedbidict_raises_on_invalid_base_type(names: tuple[str, str, str], invalid_base_type: t.Any) -> None:
    """:func:`bidict.namedbidict` should raise if given a non-bidict base_type."""
    with pytest.raises(TypeError):
        namedbidict(*names, base_type=invalid_base_type)


@given(st.NAMEDBIDICTS)
def test_namedbidict(nb: t.Any) -> None:
    """Test :func:`bidict.namedbidict` custom accessors."""
    valfor = getattr(nb, nb.valname + '_for')
    keyfor = getattr(nb, nb.keyname + '_for')
    assert all(valfor[key] == val for (key, val) in nb.items())
    assert all(keyfor[val] == key for (key, val) in nb.items())
    # The same custom accessors should work on the inverse.
    inv = nb.inv
    valfor = getattr(inv, nb.valname + '_for')
    keyfor = getattr(inv, nb.keyname + '_for')
    assert all(valfor[key] == val for (key, val) in nb.items())
    assert all(keyfor[val] == key for (key, val) in nb.items())


@skip_if_pypy
@given(st.BIDICT_TYPES)
def test_bidicts_freed_on_zero_refcount(bi_cls: t.Type[Bi]) -> None:
    """On CPython, the moment you have no more (strong) references to a bidict,
    there are no remaining (internal) strong references to it
    (i.e. no reference cycle was created between it and its inverse),
    allowing the memory to be reclaimed immediately, even with GC disabled.
    """
    gc.disable()
    try:
        bi = bi_cls()
        weak = weakref.ref(bi)
        assert weak() is not None
        del bi
        assert weak() is None
    finally:
        gc.enable()


@skip_if_pypy
@given(st.ORDERED_BIDICTS)
def test_orderedbidict_nodes_freed_on_zero_refcount(ob: OBi) -> None:
    """On CPython, the moment you have no more references to an ordered bidict,
    the refcount of each of its internal nodes drops to 0
    (i.e. the linked list of nodes does not create a reference cycle),
    allowing the memory to be reclaimed immediately.
    """
    gc.disable()
    try:
        # Make a local copy of the bidict passed in by hypothesis
        # so that its refcount actually drops to 0 when we del it below.
        ob = ob.copy()
        nodes = weakref.WeakSet(ob._sntl.iternodes())
        assert len(nodes) == len(ob)
        del ob
        assert len(nodes) == 0
    finally:
        gc.enable()


@given(st.ORDERED_BIDICTS)
def test_orderedbidict_nodes_consistent(ob: OBi) -> None:
    """The nodes in an ordered bidict's backing linked list should be the same as those in its backing mapping."""
    mapnodes = set(ob._node_by_korv.inverse)
    listnodes = set(ob._sntl.iternodes())
    assert mapnodes == listnodes


def test_abc_slots() -> None:
    """Bidict ABCs should define __slots__.

    Ref: https://docs.python.org/3/reference/datamodel.html#notes-on-using-slots
    """
    assert BidirectionalMapping.__dict__['__slots__'] == ()
    assert MutableBidirectionalMapping.__dict__['__slots__'] == ()


@given(st.BIDICTS)
def test_inv_aliases_inverse(bi: Bi) -> None:
    """bi.inv should alias bi.inverse."""
    assert bi.inverse is bi.inv
    assert bi.inv.inverse is bi.inverse.inv


@given(st.BIDICTS)
def test_inverse_readonly(bi: Bi) -> None:
    """Attempting to set the .inverse attribute should raise AttributeError."""
    with pytest.raises(AttributeError):
        bi.inverse = bi.__class__(inverted(bi))  # type: ignore
    with pytest.raises(AttributeError):
        bi.inv = bi.__class__(inverted(bi))  # type: ignore


@given(st.BIDICTS)
@example(BIDICT_TYPE_WHOSE_MODULE_HAS_REF_TO_INV_CLS({1: 'one'}).inverse)
@example(BIDICT_TYPE_WHOSE_MODULE_HAS_NO_REF_TO_INV_CLS({1: 'one'}).inverse)
def test_pickle(bi: Bi) -> None:
    """All bidicts should work with pickle."""
    pickled = pickle.dumps(bi)
    roundtripped = pickle.loads(pickled)
    assert roundtripped is roundtripped.inv.inv
    assert roundtripped.equals_order_sensitive(bi)
    assert roundtripped.inv.equals_order_sensitive(bi.inv)
    assert roundtripped.inv.inv.equals_order_sensitive(bi.inv.inv)
    assert dict(roundtripped) == dict(bi)
    roundtripped_inv = pickle.loads(pickle.dumps(bi.inv))
    assert roundtripped_inv.equals_order_sensitive(bi.inv)
    assert roundtripped_inv.inv.equals_order_sensitive(bi)
    assert roundtripped_inv.inv.inv.equals_order_sensitive(bi.inv)
    assert dict(roundtripped_inv) == dict(bi.inv)


def test_pickle_orderedbi_whose_order_disagrees_w_fwdm() -> None:
    """An OrderedBidict whose order does not match its _fwdm's should pickle with the correct order."""
    ob = OrderedBidict({0: 1, 2: 3})
    # First get ob._fwdm's order to disagree with ob's, and confirm:
    ob.inverse[1] = 4
    assert next(iter(ob.items())) == (4, 1)
    assert next(iter(ob.inverse.items())) == (1, 4)
    assert next(iter(ob._fwdm.items())) == (2, 3)
    # Now check that its order is preserved after pickling and unpickling:
    roundtripped = pickle.loads(pickle.dumps(ob))
    assert roundtripped.equals_order_sensitive(ob)


class _UserBidict(bidict[t.Any, t.Any]):
    """See :func:`test_pickle_dynamically_generated_inverse_bidict` below."""
    _invm_cls = UserDict


def test_pickle_dynamically_generated_inverse_bidict() -> None:
    """Even instances of dynamically-generated inverse bidict classes should be pickleable."""
    # The @example(BIDICT_TYPE_WHOSE_MODULE_HAS_NO_REF_TO_INV_CLS...) in test_pickle above
    # covers this, but this is an even more explicit test for clarity.

    # First pickle a non-inverse instance (whose class we have a direct reference to).
    ub = _UserBidict(one=1, two=2)
    roundtripped = pickle.loads(pickle.dumps(ub))
    assert roundtripped == ub == _UserBidict({'one': 1, 'two': 2})
    assert dict(roundtripped) == dict(ub)

    # Now for the inverse:
    assert repr(ub.inverse) == "_UserBidictInv({1: 'one', 2: 'two'})"
    # We can still pickle the inverse, even though its class, _UserBidictInv, was
    # dynamically generated, and we didn't save a reference to it named "_UserBidictInv"
    # anywhere that pickle could find it in sys.modules:
    ubinv = pickle.loads(pickle.dumps(ub.inverse))
    assert repr(ubinv) == "_UserBidictInv({1: 'one', 2: 'two'})"
    assert ub._inv_cls.__name__ not in (name for m in sys.modules for name in dir(m))


@given(st.BIDICTS)
def test_copy(bi: Bi) -> None:
    """A bidict should equal its copy."""
    cp = bi.copy()
    assert cp is not bi
    assert cp.inv is not bi.inv
    assert bi == cp
    assert bi.inv == cp.inv
    collect = list if isinstance(bi, ORDER_PRESERVING_BIDICT_TYPES) else set
    assert collect(bi.items()) == collect(cp.items())
    assert collect(bi.inv.items()) == collect(cp.inv.items())


@given(st.BIDICTS)
def test_deepcopy(bi: Bi) -> None:
    """A bidict should equal its deepcopy."""
    cp = deepcopy(bi)
    assert cp is not bi
    assert cp.inv is not bi.inv
    assert cp.inv.inv is cp
    assert cp.inv.inv is not bi
    assert bi == cp
    assert bi.inv == cp.inv
    collect = list if isinstance(bi, ORDER_PRESERVING_BIDICT_TYPES) else set
    assert collect(bi.items()) == collect(cp.items())
    assert collect(bi.inv.items()) == collect(cp.inv.items())


def test_iteritems_raises_on_too_many_args() -> None:
    """:func:`iteritems` should raise if given too many arguments."""
    with pytest.raises(TypeError):
        iteritems('too', 'many', 'args')  # type: ignore


@given(st.I_PAIRS, st.DICTS_KW_PAIRS)
def test_iteritems(arg0: t.Any, kw: t.Any) -> None:
    """:func:`iteritems` should work correctly."""
    arg0_1, arg0_2 = tee(arg0)
    it = iteritems(arg0_1, **kw)
    # Consume the first `len(arg0)` pairs, checking that they match `arg0`.
    assert all(check == expect for (check, expect) in zip(it, arg0_2))
    with pytest.raises(StopIteration):
        next(arg0_1)  # Iterating `it` should have consumed all of `arg0_1`.
    # Consume the remaining pairs, checking that they match `kw`.
    # Once min PY version required is higher, can check that the order matches `kw` too.
    assert all(kw[k] == v for (k, v) in it)
    with pytest.raises(StopIteration):
        next(it)


@given(st.L_PAIRS)
def test_inverted_pairs(pairs: t.Any) -> None:
    """:func:`bidict.inverted` should yield the inverses of a list of pairs."""
    inv = [(v, k) for (k, v) in pairs]
    assert list(inverted(pairs)) == inv
    assert list(inverted(inverted(pairs))) == pairs


@given(st.BI_AND_MAP_FROM_SAME_ND_ITEMS)
def test_inverted_bidict(bi_and_mapping: t.Any) -> None:
    """:func:`bidict.inverted` should yield the inverse items of an ordered bidict."""
    bi, mapping = bi_and_mapping
    mapping_inv = {v: k for (k, v) in mapping.items()}
    assert all(i == j for (i, j) in zip(inverted(bi), mapping_inv.items()))
    assert all(i == j for (i, j) in zip(inverted(inverted(bi)), mapping.items()))


_SET_OPS: t.Iterable[t.Callable[[t.Any, t.Any], t.Any]] = (
    op.le, op.lt, op.gt, op.ge, op.eq, op.ne, op.and_, op.or_, op.sub, op.xor, (lambda x, y: x.isdisjoint(y)),
)


@given(st.BIDICTS, st.DATA)
def test_views(bi: t.Any, data: t.Any) -> None:
    """Optimized view APIs should be equivalent to using the corresponding MappingViews from :mod:`collections.abc`."""
    for check, oracle in (bi.keys(), KeysView(bi)), (bi.values(), ValuesView(bi)), (bi.items(), ItemsView(bi)):
        assert isinstance(oracle, t.Iterable) and isinstance(oracle, t.Container)  # appease mypy
        # 0-arity methods: __len__, __iter__
        assert check.__len__() == oracle.__len__()
        assert list(check.__iter__()) == list(oracle.__iter__())
        # 1-arity methods: __contains__
        arg = data.draw(st.PAIRS if isinstance(oracle, ItemsView) else st.ATOMS)
        assert check.__contains__(arg) == oracle.__contains__(arg)
        # Methods of set-like views
        if isinstance(oracle, ValuesView):
            continue
        arg = data.draw(st.KEYSVIEW_SET_OP_ARGS if isinstance(oracle, KeysView) else st.ITEMSVIEW_SET_OP_ARGS)
        for so in _SET_OPS:
            try:
                expect = so(oracle, arg)
            except TypeError:
                with pytest.raises(TypeError):
                    so(check, arg)
            else:
                check_ = so(check, arg)
                assert check_ == expect, (check, so, arg)
            try:
                expect = so(arg, oracle)
            except TypeError:
                with pytest.raises(TypeError):
                    so(arg, check)
            else:
                check_ = so(arg, check)
                assert check_ == expect, (check, so, arg)

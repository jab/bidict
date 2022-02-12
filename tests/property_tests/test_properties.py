# Copyright 2009-2022 Joshua Bronson. All Rights Reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Property-based tests using https://hypothesis.readthedocs.io."""

import gc
import operator as op
import pickle
import sys
import unittest.mock
import weakref

from copy import deepcopy
from collections import OrderedDict, UserDict
from collections.abc import Iterable, KeysView, ValuesView, ItemsView

from itertools import tee

import pytest
from hypothesis import assume, example, given

from bidict import (
    BidictException,
    DROP_NEW, DROP_OLD, RAISE, OnDup,
    BidirectionalMapping, MutableBidirectionalMapping,
    OrderedBidict, bidict, namedbidict,
    inverted,
    DuplicationError, KeyDuplicationError, ValueDuplicationError, KeyAndValueDuplicationError,
)
from bidict._iter import iteritems_args

from . import _strategies as st
from ._types import (
    ORDER_PRESERVING_BIDICT_TYPES,
    BIDICT_TYPE_WHOSE_MODULE_HAS_REF_TO_INV_CLS,
    BIDICT_TYPE_WHOSE_MODULE_HAS_NO_REF_TO_INV_CLS,
)


require_cpython_refcounting = pytest.mark.skipif(
    sys.implementation.name != 'cpython',
    reason='Requires CPython refcounting behavior',
)


@given(st.BIDICTS, st.NON_MAPPINGS)
def test_unequal_to_non_mapping(bi, not_a_mapping):
    """Bidicts and their inverses should compare unequal to bools, ints, and other typical non-mappings."""
    assert bi != not_a_mapping
    assert bi.inv != not_a_mapping
    assert not bi == not_a_mapping
    assert not bi.inv == not_a_mapping


@given(st.BIDICTS)
def test_eq_correctly_defers_to_eq_of_non_mapping(bi):
    """Bidicts' __eq__ does not defeat non-mapping objects' __eq__, when implemented."""
    assert bi == unittest.mock.ANY
    assert unittest.mock.ANY == bi


@given(st.BI_AND_MAP_FROM_DIFF_ITEMS)
def test_unequal_to_mapping_with_different_items(bi_and_map_from_diff_items):
    """Bidicts should be unequal to mappings containing different items."""
    bi, mapping = bi_and_map_from_diff_items
    assert bi != mapping
    assert not bi == mapping


@given(st.BI_AND_MAP_FROM_SAME_ND_ITEMS)
def test_equal_to_mapping_with_same_items(bi_and_map_from_same_items):
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
def test_equal_hashables_have_same_hash(hashable_bidict_and_mapping):
    """Hashable bidicts and hashable mappings that are equal should hash to the same value."""
    bi, mapping = hashable_bidict_and_mapping
    assert bi == mapping
    assert mapping == bi
    assert hash(bi) == hash(mapping)


@given(st.BIDICTS, st.NON_BI_MAPPINGS)
@example(OrderedBidict([(1, 1), (2, 2)]), OrderedDict([(1, 1), (2, 2)]))
@example(OrderedBidict([(1, 1), (2, 2)]), OrderedDict([(2, 2), (1, 1)]))
@example(OrderedBidict({None: None}), {False: None, None: None})
def test_equals_matches_equals_order_sensitive(bi, mapping):
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
def test_equals_order_sensitive_same_items(bi_and_map_from_same_items):
    """Bidicts should be order-sensitive-equal to mappings with the same items in the same order.

    The bidict's inverse and the ordered mapping's inverse should also be order-sensitive-equal.
    """
    bi, mapping = bi_and_map_from_same_items
    assert bi.equals_order_sensitive(mapping)
    mapping_inv = OrderedDict((v, k) for (k, v) in mapping.items())
    assert bi.inv.equals_order_sensitive(mapping_inv)


@given(st.OBI_AND_OMAP_FROM_SAME_ITEMS_DIFF_ORDER)
def test_unequal_order_sensitive_same_items_different_order(ob_and_om):
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
def test_unequal_order_sensitive_non_mapping(ob, not_a_mapping):
    """Ordered bidicts should be order-sensitive-unequal to ordered mappings of diff-ordered items.

    Where both were created from the same items where no key or value was duplicated,
    but the items were ordered differently.

    The bidict's inverse and the ordered mapping's inverse should also be order-sensitive-unequal.
    """
    assert not ob.equals_order_sensitive(not_a_mapping)
    assert not ob.inv.equals_order_sensitive(not_a_mapping)


@given(st.BIDICTS, st.NON_BI_MAPPINGS)
def test_merge_operators(bi, mapping):
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
        tmp |= mapping
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
def test_setitem_with_dup_val_raises(bi, new_key, rand):
    """Setting an item whose value duplicates that of an existing item should raise ValueDuplicationError."""
    ln = len(bi)
    assume(ln > 2)
    for b in (bi, bi.inv):
        existing_val = rand.choice(list(b.inv))
        with pytest.raises(ValueDuplicationError):
            b[new_key] = existing_val
        assert len(b) == len(b.inv) == ln


@given(st.MUTABLE_BIDICTS, st.RANDOMS)
def test_setitem_with_dup_key_val_raises(bi, rand):
    """Setting an item whose key and val duplicate two different existing items raises KeyAndValueDuplicationError."""
    ln = len(bi)
    assume(ln > 2)
    for b in (bi, bi.inv):
        existing_items = rand.sample(list(b.items()), 2)
        existing_key = existing_items[0][0]
        existing_val = existing_items[1][1]
        with pytest.raises(KeyAndValueDuplicationError):
            b[existing_key] = existing_val
        assert len(b) == len(b.inv) == ln


@given(st.MUTABLE_BIDICTS, st.DIFF_ATOMS, st.RANDOMS)
def test_put_with_dup_key_raises(bi, new_val, rand):
    """Putting an item whose key duplicates that of an existing item should raise KeyDuplicationError."""
    ln = len(bi)
    assume(ln > 2)
    for b in (bi, bi.inv):
        existing_key = rand.choice(list(b))
        with pytest.raises(KeyDuplicationError):
            b.put(existing_key, new_val)
        assert len(b) == len(b.inv) == ln


@given(st.BIDICTS)
def test_bijectivity(bi):
    """b[k] == v  <==>  b.inv[v] == k"""
    for b in (bi, bi.inv):
        assert all(b.inv[v] == k for (k, v) in b.items())


@given(st.MUTABLE_BIDICTS)
def test_cleared_bidicts_have_no_items(bi):
    bi.clear()
    assert not bi
    assert len(bi) == 0


@given(st.BI_AND_CMPDICT_FROM_SAME_ITEMS, st.DATA)
def test_consistency_after_method_call(bi_and_cmp_dict, data):
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
        except TypeError:
            assert methodname == 'popitem', 'popitem should be the only method that can raise TypeError here (we sometimes pass in the wrong number of args)'
            continue
        except (KeyError, BidictException) as exc:
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
def test_putall_same_as_put_for_each_item(bi, items, on_dup):
    """*bi.putall(items) <==> for i in items: bi.put(i)* for all values of OnDup."""
    check = bi.copy()
    expect = bi.copy()
    checkexc = None
    expectexc = None
    for (key, val) in items:
        try:
            expect.put(key, val, on_dup)
        except BidictException as exc:
            expectexc = type(exc)
            expect = bi  # Bulk updates fail clean -> roll back to original state.
            break
    try:
        check.putall(items, on_dup)
    except BidictException as exc:
        checkexc = type(exc)
    assert checkexc == expectexc
    assert check == expect
    assert check.inv == expect.inv


@given(st.BI_AND_MAP_FROM_SAME_ND_ITEMS)
def test_bidict_iter(bi_and_mapping):
    """iter(bi) should yield the keys in a bidict in insertion order."""
    bi, mapping = bi_and_mapping
    assert all(i == j for (i, j) in zip(bi, mapping))


@given(st.RBI_AND_RMAP_FROM_SAME_ND_ITEMS)
def test_bidict_reversed(rb_and_rd):
    """reversed(bi) should yield the keys in a bidict in reverse insertion order."""
    rb, rd = rb_and_rd
    assert all(i == j for (i, j) in zip(reversed(rb), reversed(rd)))


@given(st.FROZEN_BIDICTS)
def test_frozenbidicts_hashable(bi):
    """Frozen bidicts can be hashed and inserted into sets and mappings."""
    assert hash(bi)
    assert {bi}
    assert {bi: bi}


@given(st.NAMEDBIDICT_NAMES_SOME_INVALID)
def test_namedbidict_raises_on_invalid_name(names):
    """:func:`bidict.namedbidict` should raise if given invalid names."""
    typename, keyname, valname = names
    with pytest.raises(ValueError):
        namedbidict(typename, keyname, valname)


@given(st.NAMEDBIDICT_NAMES_ALL_VALID)
def test_namedbidict_raises_on_same_keyname_as_valname(names):
    """:func:`bidict.namedbidict` should raise if given same keyname as valname."""
    typename, keyname, _ = names
    with pytest.raises(ValueError):
        namedbidict(typename, keyname, keyname)


@given(st.NAMEDBIDICT_NAMES_ALL_VALID, st.NON_BI_MAPPING_TYPES)
def test_namedbidict_raises_on_invalid_base_type(names, invalid_base_type):
    """:func:`bidict.namedbidict` should raise if given a non-bidict base_type."""
    with pytest.raises(TypeError):
        namedbidict(*names, base_type=invalid_base_type)


@given(st.NAMEDBIDICTS)
def test_namedbidict(nb):
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


@require_cpython_refcounting
@given(st.BIDICT_TYPES)
def test_bidicts_freed_on_zero_refcount(bi_cls):
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


@require_cpython_refcounting
@given(st.ORDERED_BIDICTS)
def test_orderedbidict_nodes_freed_on_zero_refcount(ob):
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
def test_orderedbidict_nodes_consistent(ob):
    """The nodes in an ordered bidict's backing linked list should be the same as those in its backing mapping."""
    mapnodes = set(ob._node_by_korv.inverse)
    listnodes = set(ob._sntl.iternodes())
    assert mapnodes == listnodes


def test_abc_slots():
    """Bidict ABCs should define __slots__.

    Ref: https://docs.python.org/3/reference/datamodel.html#notes-on-using-slots
    """
    assert BidirectionalMapping.__dict__['__slots__'] == ()
    assert MutableBidirectionalMapping.__dict__['__slots__'] == ()


@given(st.BIDICTS)
def test_inv_aliases_inverse(bi):
    """bi.inv should alias bi.inverse."""
    assert bi.inverse is bi.inv
    assert bi.inv.inverse is bi.inverse.inv


@given(st.BIDICTS)
def test_inverse_readonly(bi):
    """Attempting to set the .inverse attribute should raise AttributeError."""
    with pytest.raises(AttributeError):
        bi.inverse = 42
    with pytest.raises(AttributeError):
        bi.inv = 42


@given(st.BIDICTS)
@example(BIDICT_TYPE_WHOSE_MODULE_HAS_REF_TO_INV_CLS({1: 'one'}).inverse)
@example(BIDICT_TYPE_WHOSE_MODULE_HAS_NO_REF_TO_INV_CLS({1: 'one'}).inverse)
def test_pickle(bi):
    """All bidicts should work with pickle."""
    pickled = pickle.dumps(bi)
    roundtripped = pickle.loads(pickled)
    assert roundtripped is roundtripped.inv.inv
    assert roundtripped == bi
    assert roundtripped.inv == bi.inv
    assert roundtripped.inv.inv == bi.inv.inv
    assert dict(roundtripped) == dict(bi)
    roundtripped_inv = pickle.loads(pickle.dumps(bi.inv))
    assert roundtripped_inv == bi.inv
    assert roundtripped_inv.inv == bi
    assert roundtripped_inv.inv.inv == bi.inv
    assert dict(roundtripped_inv) == dict(bi.inv)


class _UserBidict(bidict):
    _invm_cls = UserDict


def test_pickle_dynamically_generated_inverse_bidict():
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
    inv_cls = ub._inv_cls
    assert inv_cls not in globals().values()
    inv_cls_name = ub._inv_cls.__name__
    assert inv_cls_name not in (name for m in sys.modules for name in dir(m))


@given(st.BIDICTS)
def test_copy(bi):
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
def test_deepcopy(bi):
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


def test_iteritems_args_raises_on_too_many_args():
    """:func:`iteritems_args` should raise if given too many arguments."""
    with pytest.raises(TypeError):
        iteritems_args('too', 'many', 'args')


@given(st.I_PAIRS, st.ODICTS_KW_PAIRS)
def test_iteritems_args(arg0, kw):
    """:func:`iteritems_args` should work correctly."""
    arg0_1, arg0_2 = tee(arg0)
    it = iteritems_args(arg0_1, **kw)
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
def test_inverted_pairs(pairs):
    """:func:`bidict.inverted` should yield the inverses of a list of pairs."""
    inv = [(v, k) for (k, v) in pairs]
    assert list(inverted(pairs)) == inv
    assert list(inverted(inverted(pairs))) == pairs


@given(st.BI_AND_MAP_FROM_SAME_ND_ITEMS)
def test_inverted_bidict(bi_and_mapping):
    """:func:`bidict.inverted` should yield the inverse items of an ordered bidict."""
    bi, mapping = bi_and_mapping
    mapping_inv = {v: k for (k, v) in mapping.items()}
    assert all(i == j for (i, j) in zip(inverted(bi), mapping_inv.items()))
    assert all(i == j for (i, j) in zip(inverted(inverted(bi)), mapping.items()))


_SET_OPS = (
    op.le, op.lt, op.gt, op.ge, op.eq, op.ne, op.and_, op.or_, op.sub, op.xor, (lambda x, y: x.isdisjoint(y)),
)


@given(st.BIDICTS, st.DATA)
def test_views(bi, data):
    """Optimized view APIs should be equivalent to using the corresponding MappingViews from :mod:`collections.abc`."""
    for check, oracle in (bi.keys(), KeysView(bi)), (bi.values(), ValuesView(bi)), (bi.items(), ItemsView(bi)):
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

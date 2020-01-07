# -*- coding: utf-8 -*-
# Copyright 2009-2020 Joshua Bronson. All Rights Reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Property-based tests using https://hypothesis.readthedocs.io."""

import gc
import pickle

from copy import deepcopy
from collections import OrderedDict
from collections.abc import Iterable
from itertools import tee
from weakref import ref

import pytest
from hypothesis import example, given

from bidict import (
    BidictException,
    DROP_NEW, OnDup,
    OrderedBidictBase, OrderedBidict, bidict, namedbidict,
    inverted,
)
from bidict.compat import PYPY
from bidict._util import _iteritems_args_kw  # pylint: disable=protected-access

from . import _strategies as st


# pylint: disable=invalid-name


@given(st.BIDICTS, st.NON_MAPPINGS)
def test_unequal_to_non_mapping(bi, not_a_mapping):
    """Bidicts and their inverses should be unequal to non-mappings."""
    assert bi != not_a_mapping
    assert bi.inv != not_a_mapping
    assert not bi == not_a_mapping
    assert not bi.inv == not_a_mapping


@given(st.BI_AND_MAP_FROM_DIFF_ITEMS)
def test_unequal_to_mapping_with_different_items(bi_and_map_from_diff_items):
    """Bidicts should be unequal to mappings containing different items."""
    bi, mapping = bi_and_map_from_diff_items
    assert bi != mapping
    assert not bi == mapping


@given(st.BI_AND_MAP_FROM_SAME_ITEMS)
def test_equal_to_mapping_with_same_items(bi_and_map_from_same_items):
    """Bidicts should be equal to mappings created from the same non-duplicating items.

    The bidict's inverse and the mapping's inverse should also be equal.
    """
    bi, mapping = bi_and_map_from_same_items
    assert bi == mapping
    assert not bi != mapping
    mapping_inv = OrderedDict((v, k) for (k, v) in mapping.items())
    assert bi.inv == mapping_inv
    assert not bi.inv != mapping_inv


@given(st.HBI_AND_HMAP_FROM_SAME_ITEMS)
def test_equal_hashables_have_same_hash(hashable_bidict_and_mapping):
    """Hashable bidicts and hashable mappings that are equal should hash to the same value."""
    bi, mapping = hashable_bidict_and_mapping
    assert bi == mapping
    assert hash(bi) == hash(mapping)


@given(st.OBI_AND_OMAP_FROM_SAME_ITEMS)
def test_equals_order_sensitive(ob_and_om):
    """Ordered bidicts should be order-sensitive-equal to ordered mappings with same nondup items.

    The bidict's inverse and the ordered mapping's inverse should also be order-sensitive-equal.
    """
    ob, om = ob_and_om
    assert ob.equals_order_sensitive(om)
    om_inv = OrderedDict((v, k) for (k, v) in om.items())
    assert ob.inv.equals_order_sensitive(om_inv)


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


@given(st.BIDICTS)
def test_bijectivity(bi):
    """b[k] == v  <==>  b.inv[v] == k"""
    for b in (bi, bi.inv):
        assert all(b.inv[v] == k for (k, v) in b.items())


@given(st.BI_AND_CMPDICT_FROM_SAME_ITEMS, st.ARGS_BY_METHOD)
def test_consistency_after_method_call(bi_and_cmp_dict, args_by_method):
    """A bidict should be left in a consistent state after calling any method, even if it raises."""
    # pylint: disable=too-many-locals
    bi_orig, cmp_dict_orig = bi_and_cmp_dict
    for (_, methodname), args in args_by_method.items():
        if not hasattr(bi_orig, methodname):
            continue
        bi = bi_orig.copy()
        method = getattr(bi, methodname)
        try:
            result = method(*args)
        except (KeyError, BidictException) as exc:
            # Call should fail clean, i.e. bi should be in the same state it was before the call.
            assertmsg = '%r did not fail clean: %r' % (method, exc)
            assert bi == bi_orig, assertmsg
            assert bi.inv == bi_orig.inv, assertmsg
        else:
            # Should get the same result as calling the same method on the compare-to dict.
            cmp_dict = cmp_dict_orig.copy()
            cmp_dict_meth = getattr(cmp_dict, methodname, None)
            if cmp_dict_meth:
                cmp_result = cmp_dict_meth(*args)
                if isinstance(cmp_result, Iterable):
                    coll = list if isinstance(bi, OrderedBidictBase) else set
                    result = coll(result)
                    cmp_result = coll(cmp_result)
                assert result == cmp_result, 'methodname=%s, args=%r' % (methodname, args)
        # Whether the call failed or succeeded, bi should pass consistency checks.
        assert len(bi) == sum(1 for _ in bi.items())
        assert len(bi.inv) == sum(1 for _ in bi.inv.items())
        assert bi == dict(bi)
        assert bi.inv == dict(bi.inv)
        assert bi == OrderedDict((k, v) for (v, k) in bi.inv.items())
        assert bi.inv == OrderedDict((v, k) for (k, v) in bi.items())


@given(st.MUTABLE_BIDICTS, st.L_PAIRS, st.ON_DUP)
# These test cases ensure coverage of all branches in [Ordered]BidictBase._undo_write
# (Hypothesis doesn't always generate examples that hit all the branches otherwise).
@example(bidict({1: 1, 2: 2}), [(1, 3), (1, 2)], OnDup(key=DROP_NEW))
@example(bidict({1: 1, 2: 2}), [(3, 1), (2, 4)], OnDup(val=DROP_NEW))
@example(bidict({1: 1, 2: 2}), [(1, 2), (1, 1)], OnDup(kv=DROP_NEW))
@example(OrderedBidict({1: 1, 2: 2}), [(1, 3), (1, 2)], OnDup(key=DROP_NEW))
@example(OrderedBidict({1: 1, 2: 2}), [(3, 1), (2, 4)], OnDup(val=DROP_NEW))
@example(OrderedBidict({1: 1, 2: 2}), [(1, 2), (1, 1)], OnDup(kv=DROP_NEW))
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


@given(st.BI_AND_CMPDICT_FROM_SAME_ITEMS)
def test_iter(bi_and_cmp_dict):
    """:meth:`bidict.BidictBase.__iter__` should yield all the keys in a bidict."""
    bi, cmp_dict = bi_and_cmp_dict
    assert set(bi) == cmp_dict.keys()


@given(st.OBI_AND_OD_FROM_SAME_ITEMS)
def test_orderedbidict_iter(ob_and_od):
    """Ordered bidict __iter__ should yield all the keys in an ordered bidict in the right order."""
    ob, od = ob_and_od
    assert all(i == j for (i, j) in zip(ob, od))


@given(st.OBI_AND_OD_FROM_SAME_ITEMS)
def test_orderedbidict_reversed(ob_and_od):
    """:meth:`bidict.OrderedBidictBase.__reversed__` should yield all the keys
    in an ordered bidict in the reverse-order they were inserted.
    """
    ob, od = ob_and_od
    assert all(i == j for (i, j) in zip(reversed(ob), reversed(od)))


@given(st.FROZEN_BIDICTS)
def test_frozenbidicts_hashable(bi):
    """Frozen bidicts can be hashed and inserted into sets and mappings."""
    # Nothing to assert; making sure these calls don't raise is sufficient.
    # pylint: disable=pointless-statement
    hash(bi)
    {bi}
    {bi: bi}


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


@given(st.NAMEDBIDICT_NAMES_ALL_VALID, st.NON_BIDICT_MAPPING_TYPES)
def test_namedbidict_raises_on_invalid_base_type(names, invalid_base_type):
    """:func:`bidict.namedbidict` should raise if given a non-bidict base_type."""
    with pytest.raises(TypeError):
        namedbidict(*names, base_type=invalid_base_type)


@given(st.NAMEDBIDICTS)
def test_namedbidict(nb):
    """Test :func:`bidict.namedbidict` custom accessors."""
    valfor = getattr(nb, nb._valname + '_for')  # pylint: disable=protected-access
    keyfor = getattr(nb, nb._keyname + '_for')  # pylint: disable=protected-access
    assert all(valfor[key] == val for (key, val) in nb.items())
    assert all(keyfor[val] == key for (key, val) in nb.items())
    # The same custom accessors should work on the inverse.
    inv = nb.inv
    valfor = getattr(inv, nb._valname + '_for')  # pylint: disable=protected-access
    keyfor = getattr(inv, nb._keyname + '_for')  # pylint: disable=protected-access
    assert all(valfor[key] == val for (key, val) in nb.items())
    assert all(keyfor[val] == key for (key, val) in nb.items())


@given(st.BIDICTS)
def test_bidict_isinv_getstate(bi):
    """All bidicts should provide ``_isinv`` and ``__getstate__``
    (or else they won't fully work as a *base_type* for :func:`namedbidict`).
    """
    # Nothing to assert; making sure these calls don't raise is sufficient.
    # pylint: disable=pointless-statement
    bi._isinv  # pylint: disable=pointless-statement,protected-access
    bi.__getstate__()  # pylint: disable=pointless-statement


# Skip this test on PyPy where reference counting isn't used to free objects immediately. See:
# https://bitbucket.org/pypy/pypy/src/dafacc4/pypy/doc/cpython_differences.rst?mode=view
# "It also means that weak references may stay alive for a bit longer than expected."
@pytest.mark.skipif(PYPY, reason='objects with 0 refcount are not freed immediately on PyPy')
@given(bi_cls=st.BIDICT_TYPES)
def test_refcycle_bidict_inverse(bi_cls):
    """When you release your last strong reference to a bidict,
    there are no remaining strong references to it
    (e.g. no reference cycle was created between it and its inverse)
    allowing the memory to be reclaimed immediately.
    """
    gc.disable()
    try:
        bi = bi_cls()
        weak = ref(bi)
        assert weak() is not None
        del bi
        assert weak() is None
    finally:
        gc.enable()


# See comment about skipping `test_refcycle_bidict_inverse` above.
@pytest.mark.skipif(PYPY, reason='objects with 0 refcount are not freed immediately on PyPy')
@given(ob_cls=st.ORDERED_BIDICT_TYPES, init_items=st.I_PAIRS_NODUP)
def test_refcycle_orderedbidict_nodes(ob_cls, init_items):
    """When you release your last strong reference to an ordered bidict,
    the refcount of each of its internal nodes drops to 0
    allowing the memory to be reclaimed immediately.
    """
    gc.disable()
    try:
        ob = ob_cls(init_items)
        node_refs = [ref(node) for node in ob._fwdm.values()]  # pylint: disable=protected-access
        assert all(r() is not None for r in node_refs)
        del ob
        assert all(r() is None for r in node_refs)
    finally:
        gc.enable()


@given(bi_cls=st.BIDICT_TYPES)
def test_slots(bi_cls):
    """See https://docs.python.org/3/reference/datamodel.html#notes-on-using-slots."""
    stop_at = {object}
    cls_by_slot = {}
    for cls in bi_cls.__mro__:
        if cls in stop_at:
            break
        slots = cls.__dict__.get('__slots__')
        assert slots is not None, 'Expected %r to define __slots__' % cls
        for slot in slots:
            seen_at = cls_by_slot.get(slot)
            assert not seen_at, '%r repeats slot %r declared first by %r' % (seen_at, slot, cls)
            cls_by_slot[slot] = cls


@given(st.BIDICTS)
def test_inv_aliases_inverse(bi):
    """bi.inv should alias bi.inverse."""
    assert bi.inverse is bi.inv
    assert bi.inv.inverse is bi.inverse.inv


@given(st.BIDICTS)
def test_pickle_roundtrips(bi):
    """A bidict should equal the result of unpickling its pickle."""
    pickled = pickle.dumps(bi)
    roundtripped = pickle.loads(pickled)
    assert roundtripped is roundtripped.inv.inv
    assert roundtripped == bi
    assert roundtripped.inv == bi.inv
    assert roundtripped.inv.inv == bi.inv.inv


@given(st.BIDICTS)
def test_deepcopy(bi):
    """A bidict should equal its deepcopy."""
    cp = deepcopy(bi)
    assert cp is not bi
    assert cp.inv.inv is cp
    assert cp.inv.inv is not bi
    assert bi == cp
    assert bi.inv == cp.inv


def test_iteritems_args_kw_raises_on_too_many_args():
    """:func:`bidict._iteritems_args_kw` should raise if given too many arguments."""
    with pytest.raises(TypeError):
        _iteritems_args_kw('too', 'many', 'args')


@given(st.I_PAIRS, st.ODICTS_KW_PAIRS)
def test_iteritems_args_kw(arg0, kw):
    """:func:`bidict._iteritems_args_kw` should work correctly."""
    arg0_1, arg0_2 = tee(arg0)
    it = _iteritems_args_kw(arg0_1, **kw)
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


@given(st.BI_AND_CMPDICT_FROM_SAME_ITEMS)
def test_inverted_bidict(bi_and_cmp_dict):
    """:func:`bidict.inverted` should yield the inverse items of a bidict."""
    bi, cmp_dict = bi_and_cmp_dict
    cmp_dict_inv = OrderedDict((v, k) for (k, v) in cmp_dict.items())
    assert set(inverted(bi)) == cmp_dict_inv.items() == bi.inv.items()
    assert set(inverted(inverted(bi))) == cmp_dict.items() == bi.inv.inv.items()


@given(st.OBI_AND_OD_FROM_SAME_ITEMS)
def test_inverted_orderedbidict(ob_and_od):
    """:func:`bidict.inverted` should yield the inverse items of an ordered bidict."""
    ob, od = ob_and_od
    od_inv = OrderedDict((v, k) for (k, v) in od.items())
    assert all(i == j for (i, j) in zip(inverted(ob), od_inv.items()))
    assert all(i == j for (i, j) in zip(inverted(inverted(ob)), od.items()))

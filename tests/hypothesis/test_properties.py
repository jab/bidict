# -*- coding: utf-8 -*-
# Copyright 2009-2019 Joshua Bronson. All Rights Reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Property-based tests using https://hypothesis.readthedocs.io."""

import gc
import pickle

from functools import reduce
from collections import OrderedDict
from weakref import ref

import pytest
from hypothesis import HealthCheck, given, settings

import _setup_hypothesis
import _strategies as st

from bidict import BidictException, OrderedBidictBase, namedbidict, inverted
from bidict.compat import (
    PY2, PYPY, collections_abc as c, iteritems, izip, viewkeys, viewitems,
)
from bidict._util import _iteritems_args_kw  # pylint: disable=protected-access


_setup_hypothesis.load_profile()


# pylint: disable=invalid-name


@given(st.BIDICTS, st.NON_MAPPINGS)
def test_unequal_to_non_mapping(bi, not_a_mapping):
    """Bidicts and their inverses should be unequal to non-mappings."""
    assert bi != not_a_mapping
    assert bi.inv != not_a_mapping
    assert not bi == not_a_mapping
    assert not bi.inv == not_a_mapping


@given(st.BIDICT_AND_MAPPING_FROM_DIFFERENT_ITEMS)
@settings(suppress_health_check=[HealthCheck.too_slow])
def test_unequal_to_mapping_with_different_items(bidict_and_mapping_from_different_items):
    """Bidicts should be unequal to mappings containing different items."""
    bi, mapping = bidict_and_mapping_from_different_items
    assert bi != mapping
    assert not bi == mapping


@given(st.BIDICT_AND_MAPPING_FROM_SAME_ITEMS_NODUP)
def test_equal_to_mapping_with_same_items(bidict_and_mapping_from_same_items_nodup):
    """Bidicts should be equal to mappings created from the same non-duplicating items.

    The bidict's inverse and the mapping's inverse should also be equal.
    """
    bi, mapping = bidict_and_mapping_from_same_items_nodup
    assert bi == mapping
    assert not bi != mapping
    mapping_inv = OrderedDict((v, k) for (k, v) in iteritems(mapping))
    assert bi.inv == mapping_inv
    assert not bi.inv != mapping_inv


@given(st.HASHABLE_BIDICT_AND_MAPPING_FROM_SAME_ITEMS_NODUP)
def test_equal_hashables_have_same_hash(hashable_bidict_and_mapping):
    """Hashable bidicts and hashable mappings that are equal should hash to the same value."""
    bi, mapping = hashable_bidict_and_mapping
    assert bi == mapping
    assert hash(bi) == hash(mapping)


@given(st.ORDERED_BIDICT_AND_ORDERED_MAPPING_FROM_SAME_ITEMS_NODUP)
def test_equals_order_sensitive(ob_and_om):
    """Ordered bidicts should be order-sensitive-equal to ordered mappings with same nondup items.

    The bidict's inverse and the ordered mapping's inverse should also be order-sensitive-equal.
    """
    ob, om = ob_and_om
    assert ob.equals_order_sensitive(om)
    om_inv = OrderedDict((v, k) for (k, v) in iteritems(om))
    assert ob.inv.equals_order_sensitive(om_inv)


@given(st.ORDERED_BIDICT_AND_ORDERED_MAPPING_FROM_SAME_ITEMS_DIFF_ORDER)
def test_unequal_order_sensitive_same_items_different_order(ob_and_om):
    """Ordered bidicts should be order-sensitive-unequal to ordered mappings of diff-ordered items.

    Where both were created from the same items where no key or value was duplicated,
    but the items were ordered differently.

    The bidict's inverse and the ordered mapping's inverse should also be order-sensitive-unequal.
    """
    ob, om = ob_and_om
    assert not ob.equals_order_sensitive(om)
    om_inv = OrderedDict((v, k) for (k, v) in iteritems(om))
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
        assert all(b.inv[v] == k for (k, v) in iteritems(b))


@given(st.BIDICT_AND_COMPARE_DICT_FROM_SAME_ITEMS_NODUP, st.ARGS_BY_METHOD)
def test_consistency_after_method_call(bi_and_cmp_dict, args_by_method):
    """A bidict should be left in a consistent state after calling any method, even if it raises."""
    # pylint: disable=too-many-locals
    bi_orig, cmp_dict_orig = bi_and_cmp_dict
    for (_, methodname), args in iteritems(args_by_method):
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
                if isinstance(cmp_result, c.Iterable):
                    coll = list if isinstance(bi, OrderedBidictBase) else set
                    result = coll(result)
                    cmp_result = coll(cmp_result)
                assert result == cmp_result, 'methodname=%s, args=%r' % (methodname, args)
        # Whether the call failed or succeeded, bi should pass consistency checks.
        assert len(bi) == sum(1 for _ in iteritems(bi))
        assert len(bi.inv) == sum(1 for _ in iteritems(bi.inv))
        assert bi == dict(bi)
        assert bi.inv == dict(bi.inv)
        assert bi == OrderedDict((k, v) for (v, k) in iteritems(bi.inv))
        assert bi.inv == OrderedDict((v, k) for (k, v) in iteritems(bi))


@given(st.MUTABLE_BIDICTS, st.LISTS_PAIRS_DUP, st.DUP_POLICIES_DICT)
def test_putall_same_as_sequential_put(bi, items, dup_policies):
    """*bi.putall(items) <==> for i in items: bi.put(i)* for all duplication policies."""
    check = bi.copy()
    expect = bi.copy()
    checkexc = None
    expectexc = None
    for (key, val) in items:
        try:
            expect.put(key, val, **dup_policies)
        except BidictException as exc:
            expectexc = type(exc)
            expect = bi  # Bulk updates fail clean -> roll back to original state.
            break
    try:
        check.putall(items, **dup_policies)
    except BidictException as exc:
        checkexc = type(exc)
    assert checkexc == expectexc
    assert check == expect
    assert check.inv == expect.inv


@given(st.BIDICT_AND_COMPARE_DICT_FROM_SAME_ITEMS_NODUP)
def test_iter(bi_and_cmp_dict):
    """:meth:`bidict.BidictBase.__iter__` should yield all the keys in a bidict."""
    bi, cmp_dict = bi_and_cmp_dict
    assert set(bi) == viewkeys(cmp_dict)


@given(st.ORDERED_BIDICT_AND_ORDERED_DICT_FROM_SAME_ITEMS_NODUP)
def test_orderedbidict_iter(ob_and_od):
    """Ordered bidict __iter__ should yield all the keys in an ordered bidict in the right order."""
    ob, od = ob_and_od
    assert all(i == j for (i, j) in izip(ob, od))


@given(st.ORDERED_BIDICT_AND_ORDERED_DICT_FROM_SAME_ITEMS_NODUP)
def test_orderedbidict_reversed(ob_and_od):
    """:meth:`bidict.OrderedBidictBase.__reversed__` should yield all the keys
    in an ordered bidict in the reverse-order they were inserted.
    """
    ob, od = ob_and_od
    assert all(i == j for (i, j) in izip(reversed(ob), reversed(od)))


@given(st.FROZEN_BIDICTS)
def test_frozenbidicts_hashable(bi):
    """Frozen bidicts can be hashed and inserted into sets and mappings."""
    # Nothing to assert; making sure these calls don't raise is sufficient.
    # pylint: disable=pointless-statement
    hash(bi)
    {bi}
    {bi: bi}


@pytest.mark.skipif(not PY2, reason='iter* methods only defined on Python 2')
@given(st.BIDICTS)
def test_iterkeys_itervals_iteritems(bi):
    """Bidicts' iter* methods should work as expected."""
    assert set(bi.iterkeys()) == bi.viewkeys()
    assert set(bi.itervalues()) == bi.viewvalues()
    assert set(bi.iteritems()) == bi.viewitems()


@pytest.mark.skipif(not PY2, reason='iter* methods only defined on Python 2')
@given(st.ORDERED_BIDICTS)
def test_orderedbidict_iterkeys_itervals_iteritems(ob):
    """Ordered bidicts' iter* methods should work as expected."""
    assert list(ob.iterkeys()) == ob.keys()
    assert list(ob.itervalues()) == ob.values()
    assert list(ob.iteritems()) == ob.items()


@given(st.st.tuples(st.TEXT, st.TEXT, st.TEXT))
def test_namedbidict_raises_on_invalid_name(names):
    """:func:`bidict.namedbidict` should raise if given invalid names."""
    typename, keyname, valname = names
    try:
        namedbidict(typename, keyname, valname)
    except ValueError:
        # Either one of the names was invalid, or the keyname and valname were not distinct.
        assert not all(map(st.NAMEDBIDICT_VALID_NAME_PAT.match, names)) or keyname == valname


@given(st.NAMEDBIDICT_3_NAMES, st.NON_BIDICT_MAPPING_TYPES)
def test_namedbidict_raises_on_invalid_base_type(names, invalid_base_type):
    """:func:`bidict.namedbidict` should raise if given a non-bidict base_type."""
    with pytest.raises(TypeError):
        namedbidict(*names, base_type=invalid_base_type)


@given(st.NAMEDBIDICTS)
def test_namedbidict(nb):
    """Test :func:`bidict.namedbidict` custom accessors."""
    valfor = getattr(nb, nb._valname + '_for')  # pylint: disable=protected-access
    keyfor = getattr(nb, nb._keyname + '_for')  # pylint: disable=protected-access
    assert all(valfor[key] == val for (key, val) in iteritems(nb))
    assert all(keyfor[val] == key for (key, val) in iteritems(nb))
    # The same custom accessors should work on the inverse.
    inv = nb.inv
    valfor = getattr(inv, nb._valname + '_for')  # pylint: disable=protected-access
    keyfor = getattr(inv, nb._keyname + '_for')  # pylint: disable=protected-access
    assert all(valfor[key] == val for (key, val) in iteritems(nb))
    assert all(keyfor[val] == key for (key, val) in iteritems(nb))


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
@given(ob_cls=st.ORDERED_BIDICT_TYPES, init_items=st.LISTS_PAIRS_NODUP)
def test_refcycle_orderedbidict_nodes(ob_cls, init_items):
    """When you release your last strong reference to an ordered bidict,
    the refcount of each of its internal nodes drops to 0
    allowing the memory to be reclaimed immediately.
    """
    gc.disable()
    try:
        some_ordered_bidict = ob_cls(init_items)
        # On Python 2, list comprehension references leak to enclosing scope -> use reduce instead:
        node_weakrefs = reduce(
            lambda acc, node: acc + [node],
            map(ref, some_ordered_bidict._fwdm.values()),  # pylint: disable=protected-access
            []
        )
        assert all(ref() is not None for ref in node_weakrefs)
        del some_ordered_bidict
        assert all(ref() is None for ref in node_weakrefs)
    finally:
        gc.enable()


@given(bi_cls=st.BIDICT_TYPES)
def test_slots(bi_cls):
    """See https://docs.python.org/3/reference/datamodel.html#notes-on-using-slots."""
    stop_at = {object}
    if PY2:
        stop_at.update({c.Mapping, c.MutableMapping})  # These don't define __slots__ in Python 2.
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
    dumps_args = {}
    # Pickling ordered bidicts in Python 2 requires a higher (non-default) protocol version.
    if PY2 and isinstance(bi, OrderedBidictBase):
        dumps_args['protocol'] = 2
    pickled = pickle.dumps(bi, **dumps_args)
    roundtripped = pickle.loads(pickled)
    assert roundtripped == bi


def test_iteritems_args_kw_raises_on_too_many_args():
    """:func:`bidict._iteritems_args_kw` should raise if given too many arguments."""
    with pytest.raises(TypeError):
        _iteritems_args_kw('too', 'many', 'args')


@given(st.LISTS_PAIRS, st.lists_pairs_nodup(elements=st.TEXT, min_size=0))  # pylint: disable=E1120
def test_iteritems_args_kw(arg0_pairs, kw_pairs):
    """:func:`bidict._iteritems_args_kw` should work correctly."""
    assert list(_iteritems_args_kw(arg0_pairs)) == list(arg0_pairs)
    assert list(_iteritems_args_kw(OrderedDict(kw_pairs))) == list(kw_pairs)
    kwdict = dict(kw_pairs)
    # Create an iterator over both arg0_pairs and kw_pairs.
    arg0_kw_items = _iteritems_args_kw(arg0_pairs, **kwdict)
    # Consume the initial (arg0) pairs of the iterator, checking they match arg0.
    assert all(check == expect for (check, expect) in izip(arg0_kw_items, arg0_pairs))
    # Consume the remaining (kw) pairs of the iterator, checking they match kw.
    assert all(kwdict[k] == v for (k, v) in arg0_kw_items)
    with pytest.raises(StopIteration):
        next(arg0_kw_items)


@given(st.LISTS_PAIRS)
def test_inverted_pairs(pairs):
    """:func:`bidict.inverted` should yield the inverses of a list of pairs."""
    inv = [(v, k) for (k, v) in pairs]
    assert list(inverted(pairs)) == inv
    assert list(inverted(inverted(pairs))) == pairs


@given(st.BIDICT_AND_COMPARE_DICT_FROM_SAME_ITEMS_NODUP)
def test_inverted_bidict(bi_and_cmp_dict):
    """:func:`bidict.inverted` should yield the inverse items of a bidict."""
    bi, cmp_dict = bi_and_cmp_dict
    cmp_dict_inv = OrderedDict((v, k) for (k, v) in iteritems(cmp_dict))
    assert set(inverted(bi)) == viewitems(cmp_dict_inv) == viewitems(bi.inv)
    assert set(inverted(inverted(bi))) == viewitems(cmp_dict) == viewitems(bi.inv.inv)


@given(st.ORDERED_BIDICT_AND_ORDERED_DICT_FROM_SAME_ITEMS_NODUP)
def test_inverted_orderedbidict(ob_and_od):
    """:func:`bidict.inverted` should yield the inverse items of an ordered bidict."""
    ob, od = ob_and_od
    od_inv = OrderedDict((v, k) for (k, v) in iteritems(od))
    assert all(i == j for (i, j) in izip(inverted(ob), iteritems(od_inv)))
    assert all(i == j for (i, j) in izip(inverted(inverted(ob)), iteritems(od)))

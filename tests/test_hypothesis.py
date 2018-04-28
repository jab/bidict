# -*- coding: utf-8 -*-
# Copyright 2018 Joshua Bronson. All Rights Reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Property-based tests using https://hypothesis.readthedocs.io."""

import gc
import pickle
import re
from collections import Hashable, Iterable, Mapping, MutableMapping, OrderedDict
from operator import itemgetter
from os import getenv
from weakref import ref

import pytest
from hypothesis import HealthCheck, assume, given, settings, strategies as strat, unlimited

from bidict import (
    BidictException, IGNORE, OVERWRITE, RAISE,
    BidirectionalMapping, bidict, OrderedBidict, OrderedBidictBase,
    frozenbidict, FrozenOrderedBidict, namedbidict, inverted)

from bidict.compat import (
    PY2, PYPY, iterkeys, itervalues, iteritems, izip)

from bidict._util import _iteritems_args_kw


settings.register_profile('default', max_examples=500, deadline=None, timeout=unlimited)
settings.register_profile('max_examples_5000', max_examples=5000, deadline=None, timeout=unlimited,
                          suppress_health_check=[HealthCheck.hung_test])

settings.load_profile(getenv('HYPOTHESIS_PROFILE', 'default'))


def prune_dup(items):
    """Given some (hypothesis-generated) items, prune any with duplicated keys or values."""
    seen_keys = set()
    seen_vals = set()
    pruned = []
    for (key, val) in items:
        if key not in seen_keys and val not in seen_vals:
            pruned.append((key, val))
        seen_keys.add(key)
        seen_vals.add(val)
    assume(len(pruned) >= len(items) // 2)
    return pruned


def ensure_dup(key=False, val=False):
    """Return a function that takes some hypothesis-generated items
    and ensures they contain the specified type of duplication.
    """
    assert key or val
    def _wrapped(items):  # noqa: E306 (expected 1 blank line before a nested definition)
        fwd = dict(items)
        if key:
            assume(len(fwd) < len(items))
        if val:
            inv = dict((v, k) for (k, v) in items)
            assume(len(inv) < len(items))
        if key and val:
            invinv = dict((v, k) for (k, v) in iteritems(inv))
            # If an item has a duplicate key and val, they must duplicate two other distinct items.
            assume(len(invinv) < len(fwd))
        return items
    return _wrapped


KEY = itemgetter(0)

MyNamedBidict = namedbidict('MyNamedBidict', 'key', 'val')
MyNamedFrozenBidict = namedbidict('MyNamedBidict', 'key', 'val', base_type=frozenbidict)
NAMEDBIDICT_VALID_NAME = re.compile('^[A-z][A-z0-9_]*$')
MUTABLE_BIDICT_TYPES = (
    bidict, OrderedBidict, MyNamedBidict)
IMMUTABLE_BIDICT_TYPES = (frozenbidict, FrozenOrderedBidict, MyNamedFrozenBidict)
ORDERED_BIDICT_TYPES = (OrderedBidict, FrozenOrderedBidict)
BIDICT_TYPES = MUTABLE_BIDICT_TYPES + IMMUTABLE_BIDICT_TYPES
MAPPING_TYPES = BIDICT_TYPES + (dict, OrderedDict)
H_BIDICT_TYPES = strat.sampled_from(BIDICT_TYPES)
H_MUTABLE_BIDICT_TYPES = strat.sampled_from(MUTABLE_BIDICT_TYPES)
H_IMMUTABLE_BIDICT_TYPES = strat.sampled_from(IMMUTABLE_BIDICT_TYPES)
H_ORDERED_BIDICT_TYPES = strat.sampled_from(ORDERED_BIDICT_TYPES)
H_MAPPING_TYPES = strat.sampled_from(MAPPING_TYPES)
H_NAMES = strat.sampled_from(('valid1', 'valid2', 'valid3', 'in-valid'))

H_DUP_POLICIES = strat.sampled_from((IGNORE, OVERWRITE, RAISE))
H_BOOLEANS = strat.booleans()
H_TEXT = strat.text()
H_NONE = strat.none()
H_IMMUTABLES = H_BOOLEANS | H_TEXT | H_NONE | strat.integers() | strat.floats(allow_nan=False)
H_NON_MAPPINGS = H_NONE
H_PAIRS = strat.tuples(H_IMMUTABLES, H_IMMUTABLES)
H_LISTS_PAIRS = strat.lists(H_PAIRS)
H_LISTS_PAIRS_NODUP = H_LISTS_PAIRS.map(prune_dup)
H_LISTS_PAIRS_DUP = (
    H_LISTS_PAIRS.map(ensure_dup(key=True)) |
    H_LISTS_PAIRS.map(ensure_dup(val=True)) |
    H_LISTS_PAIRS.map(ensure_dup(key=True, val=True)))
H_TEXT_PAIRS = strat.tuples(H_TEXT, H_TEXT)
H_LISTS_TEXT_PAIRS_NODUP = strat.lists(H_TEXT_PAIRS).map(prune_dup)
H_METHOD_ARGS = strat.sampled_from((
    # 0-arity
    ('clear', ()),
    ('popitem', ()),
    # 1-arity
    ('__delitem__', (H_IMMUTABLES,)),
    ('pop', (H_IMMUTABLES,)),
    ('setdefault', (H_IMMUTABLES,)),
    ('move_to_end', (H_IMMUTABLES,)),
    ('update', (H_LISTS_PAIRS,)),
    ('forceupdate', (H_LISTS_PAIRS,)),
    # 2-arity
    ('pop', (H_IMMUTABLES, H_IMMUTABLES)),
    ('setdefault', (H_IMMUTABLES, H_IMMUTABLES)),
    ('move_to_end', (H_IMMUTABLES, H_BOOLEANS)),
    ('__setitem__', (H_IMMUTABLES, H_IMMUTABLES)),
    ('put', (H_IMMUTABLES, H_IMMUTABLES)),
    ('forceput', (H_IMMUTABLES, H_IMMUTABLES)),
    # non-mutating
    ('__contains__', (H_IMMUTABLES,)),
    ('__copy__', ()),
    ('__getitem__', (H_IMMUTABLES,)),
    ('__iter__', ()),
    ('__len__', ()),
    ('copy', ()),
    ('get', (H_IMMUTABLES,)),
    ('keys', ()),
    ('items', ()),
    ('values', ()),
    ('iterkeys', ()),
    ('iteritems', ()),
    ('itervalues', ()),
    ('viewkeys', ()),
    ('viewitems', ()),
    ('viewvalues', ()),
))


@given(bi_cls=H_BIDICT_TYPES, other_cls=H_MAPPING_TYPES, not_a_mapping=H_NON_MAPPINGS,
       init_items=H_LISTS_PAIRS_NODUP, init_unequal=H_LISTS_PAIRS_NODUP)
def test_eq_ne_hash(bi_cls, other_cls, init_items, init_unequal, not_a_mapping):
    """Test various equality comparisons and hashes between bidicts and other objects."""
    # pylint: disable=too-many-locals
    some_bidict = bi_cls(init_items)
    other_equal = other_cls(init_items)
    other_equal_inv = getattr(other_equal, 'inv',
                              OrderedDict((v, k) for (k, v) in iteritems(other_equal)))

    bidict_is_ordered = isinstance(some_bidict, OrderedBidictBase)
    other_is_ordered = issubclass(other_cls, (OrderedBidictBase, OrderedDict))
    collection = list if bidict_is_ordered and other_is_ordered else set

    both_hashable = all(isinstance(i, Hashable) for i in (some_bidict, other_equal))
    has_eq_order_sens = getattr(bi_cls, 'equals_order_sensitive', None)

    other_unequal = other_cls(init_unequal)
    other_unequal_inv = getattr(other_unequal, 'inv',
                                OrderedDict((v, k) for (k, v) in iteritems(other_unequal)))

    assert some_bidict == other_equal
    assert not some_bidict != other_equal
    assert some_bidict.inv == other_equal_inv
    assert not some_bidict.inv != other_equal_inv

    assert collection(iteritems(some_bidict)) == collection(iteritems(other_equal))
    assert collection(iteritems(some_bidict.inv)) == collection(iteritems(other_equal_inv))

    if both_hashable:
        assert hash(some_bidict) == hash(other_equal)

    if has_eq_order_sens and other_is_ordered:
        assert some_bidict.equals_order_sensitive(other_equal)
        assert some_bidict.inv.equals_order_sensitive(other_equal_inv)

        assume(init_items != init_unequal)
        other_unequal = other_cls(init_unequal)
        assert not some_bidict.equals_order_sensitive(other_unequal)
        other_unequal_inv = getattr(other_unequal, 'inv',
                                    OrderedDict((v, k) for (k, v) in iteritems(other_unequal)))
        assert not some_bidict.inv.equals_order_sensitive(other_unequal_inv)

    assume(set(init_items) != set(init_unequal))

    assert some_bidict != other_unequal
    assert not some_bidict == other_unequal
    assert some_bidict.inv != other_unequal_inv
    assert not some_bidict.inv == other_unequal_inv

    assert collection(iteritems(some_bidict)) != collection(iteritems(other_unequal))
    assert collection(iteritems(some_bidict.inv)) != collection(iteritems(other_unequal_inv))

    assert not some_bidict == not_a_mapping
    assert not some_bidict.inv == not_a_mapping
    assert some_bidict != not_a_mapping
    assert some_bidict.inv != not_a_mapping
    if has_eq_order_sens:
        assert not some_bidict.equals_order_sensitive(not_a_mapping)
        assert not some_bidict.inv.equals_order_sensitive(not_a_mapping)


@given(bi_cls=H_BIDICT_TYPES, init_items=H_LISTS_PAIRS_NODUP)
def test_bijectivity(bi_cls, init_items):
    """b[k] == v  <==>  b.inv[v] == k"""
    some_bidict = bi_cls(init_items)
    ordered = isinstance(some_bidict, OrderedBidictBase)
    collection = list if ordered else set
    keys = collection(iterkeys(some_bidict))
    vals = collection(itervalues(some_bidict))
    fwd_by_keys = collection(some_bidict[k] for k in iterkeys(some_bidict))
    inv_by_vals = collection(some_bidict.inv[v] for v in itervalues(some_bidict))
    assert keys == inv_by_vals
    assert vals == fwd_by_keys
    inv = some_bidict.inv
    inv_keys = collection(iterkeys(inv))
    inv_vals = collection(itervalues(inv))
    inv_fwd_by_keys = collection(inv[k] for k in iterkeys(inv))
    inv_inv_by_vals = collection(inv.inv[v] for v in itervalues(inv))
    assert inv_keys == inv_inv_by_vals
    assert inv_vals == inv_fwd_by_keys


@given(bi_cls=H_BIDICT_TYPES, init_items=H_LISTS_PAIRS_NODUP,
       setinv=H_BOOLEANS, method_args=H_METHOD_ARGS, data=strat.data())
def test_consistency(bi_cls, init_items, setinv, method_args, data):
    """Every bidict should be left in a consistent state after calling
    any method on it that it provides, even if the call raises.
    """
    # pylint: disable=too-many-locals
    methodname, hs_args = method_args
    method = getattr(bi_cls, methodname, None)
    if not method:
        return
    args = tuple(data.draw(i) for i in hs_args)
    bi_called = bi_cls(init_items)
    bi_pristine = bi_cls(init_items)
    if setinv:
        bi_called = bi_called.inv
        bi_pristine = bi_pristine.inv
        init_items = [(v, k) for (k, v) in init_items]
    try:
        result = method(bi_called, *args)
    except (KeyError, BidictException) as exc:
        # Call should fail clean, i.e. bi_called should be in the same state it was before the call.
        assertmsg = '%r did not fail clean: %r' % (method, exc)
        assert bi_called == bi_pristine, assertmsg
        assert bi_called.inv == bi_pristine.inv, assertmsg
    else:
        ordered = issubclass(bi_cls, OrderedBidictBase)
        dict_cls = OrderedDict if ordered else dict
        dict_meth = getattr(dict_cls, methodname, None)
        if dict_meth:
            compare_dict = dict_cls(init_items)
            dict_result = dict_meth(compare_dict, *args)
            if isinstance(dict_result, Iterable):
                collection = list if ordered else set
                result = collection(result)
                dict_result = collection(dict_result)
            assert result == dict_result
    # Whether the call failed or succeeded, bi_called should pass consistency checks.
    assert len(bi_called) == sum(1 for _ in iteritems(bi_called))
    assert len(bi_called.inv) == sum(1 for _ in iteritems(bi_called.inv))
    assert bi_called == dict(bi_called)
    assert bi_called.inv == dict(bi_called.inv)
    assert bi_called == OrderedDict((k, v) for (v, k) in iteritems(bi_called.inv))
    assert bi_called.inv == OrderedDict((v, k) for (k, v) in iteritems(bi_called))


@given(bi_cls=H_MUTABLE_BIDICT_TYPES,
       init_items=H_LISTS_PAIRS_NODUP,
       update_items=H_LISTS_PAIRS_DUP,
       on_dup_key=H_DUP_POLICIES, on_dup_val=H_DUP_POLICIES, on_dup_kv=H_DUP_POLICIES)
def test_dup_policies_bulk(bi_cls, init_items, update_items, on_dup_key, on_dup_val, on_dup_kv):
    """Attempting a bulk update with *update_items* should yield the same result as
    attempting to set each of the items sequentially
    while respecting the duplication policies that are in effect.
    """
    dup_policies = dict(on_dup_key=on_dup_key, on_dup_val=on_dup_val, on_dup_kv=on_dup_kv)
    bi_init = bi_cls(init_items)
    expect = bi_init.copy()
    expectexc = None
    for (key, val) in update_items:
        try:
            expect.put(key, val, **dup_policies)
        except BidictException as exc:
            expectexc = type(exc)
            expect = bi_init  # bulk updates fail clean
            break
    check = bi_init.copy()
    checkexc = None
    try:
        check.putall(update_items, **dup_policies)
    except BidictException as exc:
        checkexc = type(exc)
    assert checkexc == expectexc
    assert check == expect
    assert check.inv == expect.inv


@given(bi_cls=H_BIDICT_TYPES, init_items=H_LISTS_PAIRS_NODUP)
def test_bidict_iter(bi_cls, init_items):
    """:meth:`bidict.BidictBase.__iter__` should yield all the keys in a bidict."""
    some_bidict = bi_cls(init_items)
    assert set(some_bidict) == set(iterkeys(some_bidict)) == set(KEY(pair) for pair in init_items)


@given(ob_cls=H_ORDERED_BIDICT_TYPES, init_items=H_LISTS_PAIRS_NODUP)
def test_orderedbidict_iter(ob_cls, init_items):
    """:meth:`bidict.OrderedBidictBase.__iter__` should yield all the keys
    in an ordered bidict in the order they were inserted.
    """
    some_bidict = ob_cls(init_items)
    key_iters = (some_bidict, iterkeys(some_bidict), (KEY(pair) for pair in init_items))
    assert all(i == j == k for (i, j, k) in izip(*key_iters))


@given(ob_cls=H_ORDERED_BIDICT_TYPES, init_items=H_LISTS_PAIRS_NODUP)
def test_orderedbidict_reversed(ob_cls, init_items):
    """:meth:`bidict.OrderedBidictBase.__reversed__` should yield all the keys
    in an ordered bidict in the reverse-order they were inserted.
    """
    some_bidict = ob_cls(init_items)
    key_seqs = (some_bidict, list(iterkeys(some_bidict)), [KEY(pair) for pair in init_items])
    key_seqs_rev = (reversed(i) for i in key_seqs)
    assert all(i == j == k for (i, j, k) in izip(*key_seqs_rev))


@given(fb_cls=H_IMMUTABLE_BIDICT_TYPES)
def test_frozenbidicts_hashable(fb_cls):
    """Immutable bidicts can be hashed and inserted into sets and mappings."""
    some_bidict = fb_cls()
    # Nothing to assert; making sure these calls don't raise TypeError is sufficient.
    hash(some_bidict)  # pylint: disable=pointless-statement
    {some_bidict}  # pylint: disable=pointless-statement
    {some_bidict: some_bidict}  # pylint: disable=pointless-statement


@pytest.mark.skipif(not PY2, reason='iter* methods only defined on Python 2')
@given(bi_cls=H_BIDICT_TYPES)
def test_iterkeys_vals_items(bi_cls):
    """Frozen bidicts' iter* methods work as expected."""
    some_bidict = bi_cls()
    ordered = issubclass(bi_cls, OrderedBidictBase)
    collection = list if ordered else set
    assert collection(some_bidict.iterkeys()) == collection(some_bidict.keys())
    assert collection(some_bidict.itervalues()) == collection(some_bidict.values())
    assert collection(some_bidict.iteritems()) == collection(some_bidict.items())


@given(base_type=H_MAPPING_TYPES, init_items=H_LISTS_PAIRS_NODUP, data=strat.data())
def test_namedbidict(base_type, init_items, data):
    """Test the :func:`bidict.namedbidict` factory and custom accessors."""
    names = typename, keyname, valname = [data.draw(H_NAMES) for _ in range(3)]
    try:
        nbcls = namedbidict(typename, keyname, valname, base_type=base_type)
    except ValueError:
        # Either one of the names was invalid, or the keyname and valname were not distinct.
        assert not all(map(NAMEDBIDICT_VALID_NAME.match, names)) or keyname == valname
        return
    except TypeError:
        # The base type must not have been a BidirectionalMapping.
        assert not issubclass(base_type, BidirectionalMapping)
        return
    assume(init_items)
    instance = nbcls(init_items)
    valfor = getattr(instance, valname + '_for')
    keyfor = getattr(instance, keyname + '_for')
    assert all(valfor[key] == val for (key, val) in iteritems(instance))
    assert all(keyfor[val] == key for (key, val) in iteritems(instance))
    # The same custom accessors should work on the inverse.
    inv = instance.inv
    valfor = getattr(inv, valname + '_for')
    keyfor = getattr(inv, keyname + '_for')
    assert all(valfor[key] == val for (key, val) in iteritems(instance))
    assert all(keyfor[val] == key for (key, val) in iteritems(instance))


@given(bi_cls=H_BIDICT_TYPES)
def test_bidict_isinv(bi_cls):
    """All bidict types should provide ``_isinv`` and ``__getstate__``
    (or else they won't fully work as a *base_type* for :func:`namedbidict`).
    """
    some_bidict = bi_cls()
    # Nothing to assert; making sure these calls don't raise is sufficient.
    some_bidict._isinv  # pylint: disable=pointless-statement,protected-access
    some_bidict.__getstate__()  # pylint: disable=pointless-statement


# Skip this test on PyPy where reference counting isn't used to free objects immediately. See:
# http://doc.pypy.org/en/latest/cpython_differences.html#differences-related-to-garbage-collection-strategies
# "It also means that weak references may stay alive for a bit longer than expected."
@pytest.mark.skipif(PYPY, reason='objects with 0 refcount are not freed immediately on PyPy')
@given(bi_cls=H_BIDICT_TYPES)
def test_refcycle_bidict_inverse(bi_cls):
    """When you release your last strong reference to a bidict,
    there are no remaining strong references to it
    (e.g. no reference cycle was created between it and its inverse)
    allowing the memory to be reclaimed immediately.
    """
    gc.disable()
    try:
        some_bidict = bi_cls()
        weak = ref(some_bidict)
        assert weak() is not None
        del some_bidict
        assert weak() is None
    finally:
        gc.enable()


# See comment about skipping `test_refcycle_bidict_inverse` above.
@pytest.mark.skipif(PYPY, reason='objects with 0 refcount are not freed immediately on PyPy')
@given(ob_cls=H_ORDERED_BIDICT_TYPES, init_items=H_LISTS_PAIRS_NODUP)
def test_refcycle_obidict_nodes(ob_cls, init_items):
    """When you release your last strong reference to an ordered bidict,
    the refcount of each of its internal nodes drops to 0
    allowing the memory to be reclaimed immediately.
    """
    assume(init_items)
    gc.disable()
    try:
        some_ordered_bidict = ob_cls(init_items)
        # pylint: disable=protected-access
        node_weakrefs = [ref(node) for node in some_ordered_bidict._fwdm.values()]
        if PY2:
            # On Python 2, list comprehension references leak to the enclosing scope,
            # so this reference must be released for the refcount to drop to 0.
            del node  # pylint: disable=undefined-variable
        assert all(ref() is not None for ref in node_weakrefs)
        del some_ordered_bidict
        assert all(ref() is None for ref in node_weakrefs)
    finally:
        gc.enable()


@given(bi_cls=H_BIDICT_TYPES)
def test_slots(bi_cls):
    """See https://docs.python.org/3/reference/datamodel.html#notes-on-using-slots."""
    stop_at = {object}
    if PY2:
        stop_at.update({Mapping, MutableMapping})  # These don't define __slots__ in Python 2.
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


@given(bi_cls=H_BIDICT_TYPES, init_items=H_LISTS_PAIRS_NODUP)
def test_pickle_roundtrips(bi_cls, init_items):
    """A bidict should equal the result of unpickling its pickle."""
    some_bidict = bi_cls(init_items)
    dumps_args = {}
    # Pickling ordered bidicts in Python 2 requires a higher (non-default) protocol version.
    if PY2 and issubclass(bi_cls, OrderedBidictBase):
        dumps_args['protocol'] = 2
    pickled = pickle.dumps(some_bidict, **dumps_args)
    roundtripped = pickle.loads(pickled)
    assert roundtripped == some_bidict


@given(arg0_pairs=H_LISTS_PAIRS, kw_pairs=H_LISTS_TEXT_PAIRS_NODUP)
def test_iter_items_arg_kw(arg0_pairs, kw_pairs):
    """Test that :func:`bidict.items` works correctly."""
    with pytest.raises(TypeError):
        _iteritems_args_kw('too', 'many', 'args')
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


@given(bi_cls=H_BIDICT_TYPES, init_items=H_LISTS_PAIRS_NODUP)
def test_inverted(bi_cls, init_items):
    """Test that :func:`bidict.inverted` works correctly."""
    inv_items = [(v, k) for (k, v) in init_items]
    assert list(inverted(init_items)) == inv_items
    assert list(inverted(inverted(init_items))) == init_items
    some_bidict = bi_cls(init_items)
    inv_bidict = bi_cls(inv_items)
    assert some_bidict.inv == inv_bidict
    assert set(inverted(some_bidict)) == set(inv_items)
    assert bi_cls(inverted(inv_bidict)) == some_bidict

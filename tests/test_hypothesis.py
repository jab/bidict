# -*- coding: utf-8 -*-
# Copyright 2018 Joshua Bronson. All Rights Reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Property-based tests using https://hypothesis.readthedocs.io."""

import gc
import pickle
from collections import Hashable, Mapping, MutableMapping, OrderedDict
from os import getenv
from weakref import ref

import pytest
from hypothesis import assume, given, settings, strategies as strat
from bidict import (
    BidictException,
    IGNORE, OVERWRITE, RAISE,
    bidict, namedbidict, OrderedBidict,
    frozenbidict, FrozenOrderedBidict)
from bidict.compat import PY2, PYPY, iterkeys, itervalues, iteritems


settings.register_profile('default', settings(max_examples=200, deadline=None))
settings.load_profile(getenv('HYPOTHESIS_PROFILE', 'default'))


def inv_od(items):
    """An OrderedDict containing the inverse of each item in *items*."""
    return OrderedDict((v, k) for (k, v) in items)


def ensure_no_dup(items):
    """Given some hypothesis-generated items, prune any with duplicated keys or values."""
    pruned = list(iteritems(inv_od(iteritems(inv_od(items)))))
    assume(len(pruned) >= len(items) // 2)
    return pruned


def ensure_dup(key=False, val=False):
    """Return a function that takes some hypothesis-generated items
    and ensures they contain the specified type of duplication."""
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


class OverwritingBidict(bidict):
    """A :class:`~bidict.bidict` subclass with default OVERWRITE behavior."""
    __slots__ = ()
    on_dup_val = OVERWRITE


class OverwritingOrderedBidict(OrderedBidict):
    """An :class:`~bidict.OrderedBidict` subclass with a default OVERWRITE behavior."""
    __slots__ = ()
    on_dup_val = OVERWRITE


MyNamedBidict = namedbidict('MyNamedBidict', 'key', 'val')
MyNamedFrozenBidict = namedbidict('MyNamedBidict', 'key', 'val', base_type=frozenbidict)
MUTABLE_BIDICT_TYPES = (
    bidict, OverwritingBidict, OrderedBidict, OverwritingOrderedBidict, MyNamedBidict)
IMMUTABLE_BIDICT_TYPES = (frozenbidict, FrozenOrderedBidict, MyNamedFrozenBidict)
BIDICT_TYPES = MUTABLE_BIDICT_TYPES + IMMUTABLE_BIDICT_TYPES
MAPPING_TYPES = BIDICT_TYPES + (dict, OrderedDict)
HS_BIDICT_TYPES = strat.sampled_from(BIDICT_TYPES)
HS_MUTABLE_BIDICT_TYPES = strat.sampled_from(MUTABLE_BIDICT_TYPES)
HS_MAPPING_TYPES = strat.sampled_from(MAPPING_TYPES)

HS_DUP_POLICIES = strat.sampled_from((IGNORE, OVERWRITE, RAISE))
HS_BOOLEANS = strat.booleans()
HS_IMMUTABLES = HS_BOOLEANS | strat.none() | strat.integers()
HS_PAIRS = strat.tuples(HS_IMMUTABLES, HS_IMMUTABLES)
HS_LISTS_PAIRS = strat.lists(HS_PAIRS)
HS_LISTS_PAIRS_NODUP = HS_LISTS_PAIRS.map(ensure_no_dup)
HS_LISTS_PAIRS_DUP = (
    HS_LISTS_PAIRS.map(ensure_dup(key=True)) |
    HS_LISTS_PAIRS.map(ensure_dup(val=True)) |
    HS_LISTS_PAIRS.map(ensure_dup(key=True, val=True)))
HS_METHOD_ARGS = strat.sampled_from((
    # 0-arity
    ('clear', ()),
    ('popitem', ()),
    # 1-arity
    ('__delitem__', (HS_IMMUTABLES,)),
    ('pop', (HS_IMMUTABLES,)),
    ('setdefault', (HS_IMMUTABLES,)),
    ('move_to_end', (HS_IMMUTABLES,)),
    ('update', (HS_LISTS_PAIRS,)),
    ('forceupdate', (HS_LISTS_PAIRS,)),
    # 2-arity
    ('pop', (HS_IMMUTABLES, HS_IMMUTABLES)),
    ('setdefault', (HS_IMMUTABLES, HS_IMMUTABLES)),
    ('move_to_end', (HS_IMMUTABLES, HS_BOOLEANS)),
    ('__setitem__', (HS_IMMUTABLES, HS_IMMUTABLES)),
    ('put', (HS_IMMUTABLES, HS_IMMUTABLES)),
    ('forceput', (HS_IMMUTABLES, HS_IMMUTABLES)),
))


def assert_items_match(map1, map2, assertmsg=None):
    """Ensure map1 and map2 contain the same items (and in the same order, if they're ordered)."""
    if assertmsg is None:
        assertmsg = repr((map1, map2))
    both_ordered = all(isinstance(m, (OrderedDict, FrozenOrderedBidict)) for m in (map1, map2))
    canon = list if both_ordered else set
    assert canon(iteritems(map1)) == canon(iteritems(map2)), assertmsg


@given(data=strat.data())
def test_eq_ne_hash(data):
    """Test various equality comparisons and hashes between bidicts and other objects."""
    bi_cls = data.draw(HS_BIDICT_TYPES)
    init = data.draw(HS_LISTS_PAIRS_NODUP)
    some_bidict = bi_cls(init)
    other_cls = data.draw(HS_MAPPING_TYPES)
    other_equal = other_cls(init)
    other_equal_inv = inv_od(iteritems(other_equal))
    assert some_bidict == other_equal
    assert not some_bidict != other_equal
    assert some_bidict.inv == other_equal_inv
    assert not some_bidict.inv != other_equal_inv
    has_eq_order_sens = getattr(bi_cls, 'equals_order_sensitive', None)
    other_is_ordered = getattr(other_cls, '__reversed__', None)
    if has_eq_order_sens and other_is_ordered:
        assert some_bidict.equals_order_sensitive(other_equal)
        assert some_bidict.inv.equals_order_sensitive(other_equal_inv)
    both_hashable = issubclass(bi_cls, Hashable) and issubclass(other_cls, Hashable)
    if both_hashable:
        assert hash(some_bidict) == hash(other_equal)

    unequal_init = data.draw(HS_LISTS_PAIRS_NODUP)
    assume(unequal_init != init)
    other_unequal = other_cls(unequal_init)
    other_unequal_inv = inv_od(iteritems(other_unequal))
    assert some_bidict != other_unequal
    assert not some_bidict == other_unequal
    assert some_bidict.inv != other_unequal_inv
    assert not some_bidict.inv == other_unequal_inv
    if has_eq_order_sens:
        assert not some_bidict.equals_order_sensitive(other_unequal)
        assert not some_bidict.inv.equals_order_sensitive(other_unequal_inv)

    not_a_mapping = 'not a mapping'
    assert not some_bidict == not_a_mapping
    assert not some_bidict.inv == not_a_mapping
    assert some_bidict != not_a_mapping
    assert some_bidict.inv != not_a_mapping
    if has_eq_order_sens:
        assert not some_bidict.equals_order_sensitive(not_a_mapping)
        assert not some_bidict.inv.equals_order_sensitive(not_a_mapping)


@given(bi_cls=HS_BIDICT_TYPES, init=HS_LISTS_PAIRS_NODUP)
def test_bijectivity(bi_cls, init):
    """*b[k] == v  <==>  b.inv[v] == k*"""
    some_bidict = bi_cls(init)
    ordered = issubclass(bi_cls, FrozenOrderedBidict)
    canon = list if ordered else set
    keys = canon(iterkeys(some_bidict))
    vals = canon(itervalues(some_bidict))
    fwd_by_keys = canon(some_bidict[k] for k in iterkeys(some_bidict))
    inv_by_vals = canon(some_bidict.inv[v] for v in itervalues(some_bidict))
    assert keys == inv_by_vals
    assert vals == fwd_by_keys
    inv = some_bidict.inv
    inv_keys = canon(iterkeys(inv))
    inv_vals = canon(itervalues(inv))
    inv_fwd_by_keys = canon(inv[k] for k in iterkeys(inv))
    inv_inv_by_vals = canon(inv.inv[v] for v in itervalues(inv))
    assert inv_keys == inv_inv_by_vals
    assert inv_vals == inv_fwd_by_keys


@given(bi_cls=HS_MUTABLE_BIDICT_TYPES, init=HS_LISTS_PAIRS_NODUP,
       method_args=HS_METHOD_ARGS, data=strat.data())
def test_consistency_after_mutation(bi_cls, init, method_args, data):
    """Call every mutating method on every bidict that implements it,
    and ensure the bidict is left in a consistent state afterward.
    """
    methodname, hs_args = method_args
    method = getattr(bi_cls, methodname, None)
    if not method:
        return
    args = tuple(data.draw(i) for i in hs_args)
    bi_init = bi_cls(init)
    bi_clone = bi_init.copy()
    assert_items_match(bi_init, bi_clone)
    try:
        method(bi_clone, *args)
    except (KeyError, BidictException) as exc:
        # Call should fail clean, i.e. bi_clone should be in the same state it was before the call.
        assertmsg = '%r did not fail clean: %r' % (method, exc)
        assert_items_match(bi_clone, bi_init, assertmsg)
        assert_items_match(bi_clone.inv, bi_init.inv, assertmsg)
    # Whether the call failed or succeeded, bi_clone should pass consistency checks.
    assert len(bi_clone) == sum(1 for _ in iteritems(bi_clone))
    assert len(bi_clone) == sum(1 for _ in iteritems(bi_clone.inv))
    assert_items_match(bi_clone, dict(bi_clone))
    assert_items_match(bi_clone.inv, dict(bi_clone.inv))
    assert_items_match(bi_clone, inv_od(iteritems(bi_clone.inv)))
    assert_items_match(bi_clone.inv, inv_od(iteritems(bi_clone)))


@given(bi_cls=HS_MUTABLE_BIDICT_TYPES, init=HS_LISTS_PAIRS_NODUP, items=HS_LISTS_PAIRS_DUP,
       on_dup_key=HS_DUP_POLICIES, on_dup_val=HS_DUP_POLICIES, on_dup_kv=HS_DUP_POLICIES)
def test_dup_policies_bulk(bi_cls, init, items, on_dup_key, on_dup_val, on_dup_kv):
    """Attempting a bulk update with *items* should yield the same result as
    attempting to set each of the items sequentially
    while respecting the duplication policies that are in effect.
    """
    bi_init = bi_cls(init)
    expect = bi_init.copy()
    expectexc = None
    for (key, val) in items:
        try:
            expect.put(key, val, on_dup_key=on_dup_key, on_dup_val=on_dup_val, on_dup_kv=on_dup_kv)
        except BidictException as exc:
            expectexc = exc
            expect = bi_init  # bulk updates fail clean
            break
    check = bi_init.copy()
    checkexc = None
    try:
        check.putall(items, on_dup_key=on_dup_key, on_dup_val=on_dup_val, on_dup_kv=on_dup_kv)
    except BidictException as exc:
        checkexc = exc
    assert type(checkexc) == type(expectexc)  # pylint: disable=unidiomatic-typecheck
    assert_items_match(check, expect)
    assert_items_match(check.inv, expect.inv)


# Skip this test on PyPy where reference counting isn't used to free objects immediately. See:
# http://doc.pypy.org/en/latest/cpython_differences.html#differences-related-to-garbage-collection-strategies
# "It also means that weak references may stay alive for a bit longer than expected."
@pytest.mark.skipif(PYPY, reason='objects with 0 refcount not freed immediately on PyPy')
@given(bi_cls=HS_BIDICT_TYPES)
def test_no_reference_cycles(bi_cls):
    """When you delete your last strong reference to a bidict,
    there are no remaining strong references to it
    (e.g. no reference cycle was created between it and its inverse)
    so its memory can be reclaimed immediately.
    """
    gc.disable()
    some_bidict = bi_cls()
    weak = ref(some_bidict)
    assert weak() is not None
    del some_bidict
    assert weak() is None
    gc.enable()


@given(bi_cls=HS_BIDICT_TYPES)
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


@given(bi_cls=HS_BIDICT_TYPES, init=HS_LISTS_PAIRS_NODUP)
def test_pickle_roundtrips(bi_cls, init):
    """A bidict should equal the result of unpickling its pickle."""
    some_bidict = bi_cls(init)
    dumps_args = {}
    # Pickling ordered bidicts in Python 2 requires a higher (non-default) protocol version.
    if PY2 and issubclass(bi_cls, FrozenOrderedBidict):
        dumps_args['protocol'] = 2
    pickled = pickle.dumps(some_bidict, **dumps_args)
    roundtripped = pickle.loads(pickled)
    assert roundtripped == some_bidict

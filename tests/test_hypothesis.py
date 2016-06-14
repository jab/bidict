"""
Property-based tests using https://warehouse.python.org/project/hypothesis/
"""

from bidict._common import _dedup_update
from bidict import (
    OrderedBidirectionalMapping, IGNORE, OVERWRITE, RAISE,
    KeyNotUniqueError, ValueNotUniqueError, KeyAndValueNotUniqueError,
    bidict, loosebidict, looseorderedbidict, orderedbidict)
from bidict.compat import iteritems, viewitems
from collections import Mapping, OrderedDict
from hypothesis import assume, given, settings
from hypothesis.strategies import dictionaries, integers, lists, tuples
from os import getenv
import pytest


# https://groups.google.com/d/msg/hypothesis-users/8FVs--1yUl4/JEkJ02euEwAJ
settings.register_profile('default', settings(strict=True))
settings.load_profile(getenv('HYPOTHESIS_PROFILE', 'default'))


def inv(d):
    return {v: k for (k, v) in iteritems(d)}


def prune_dup_vals(d):
    pruned = inv(inv(d))
    assume(len(pruned) >= len(d) // 2)
    return pruned


ondupbehaviors = (IGNORE, OVERWRITE, RAISE)
mutable_bidict_types = (bidict, loosebidict, looseorderedbidict, orderedbidict)
mutating_methods_by_arity = {
    0: ('clear', 'popitem',),
    1: ('__delitem__', 'pop', 'setdefault', 'move_to_end',),
    2: ('__setitem__', 'pop', 'put', 'forceput', 'setdefault',),
    -1: ('update', 'forceupdate',),
}
immutable = integers()
# To test with more immutable types, can use the following, but it slows down
# the tests without finding more bugs:
# sz = dict(average_size=2)
# immu_atom = none() | booleans() | integers() | floats(allow_nan=False) | text(**sz) | binary(**sz)
# immu_coll = lambda e: frozensets(e, **sz) | lists(e, **sz).map(tuple)
# immutable = recursive(immu_atom, immu_coll)
itemlists = lists(tuples(immutable, immutable))
d = dictionaries(immutable, immutable).map(prune_dup_vals)


@given(d)
def test_equality(d):
    i = inv(d)
    b = bidict(d)
    assert b == d
    assert b.inv == i
    assert not b != d
    assert not b.inv != i


@given(d)
def test_bidirectional_mappings(d):
    b = bidict(d)
    for k, v in iteritems(b):
        assert k == b.inv[v]
    for v, k in iteritems(b.inv):
        assert v == b[k]


@given(d)
def test_len(d):
    b = bidict(d)
    assert len(b) == len(b.inv) == len(d)


@pytest.mark.parametrize('arity,methodname',
    [(a, m) for (a, ms) in iteritems(mutating_methods_by_arity) for m in ms])
@pytest.mark.parametrize('B', mutable_bidict_types)
@given(d=d, arg1=immutable, arg2=immutable, itemlist=itemlists)
def test_consistency_after_mutation(arity, methodname, B, d, arg1, arg2, itemlist):
    loose = issubclass(B, loosebidict)
    ordered = issubclass(B, OrderedBidirectionalMapping)
    b = B(d)
    assert dict(b) == inv(b.inv)
    assert dict(b.inv) == inv(b)
    method = getattr(B, methodname, None)
    if not method:
        return
    args = []
    if arity == -1:
        args.append(itemlist)
    else:
        if arity > 0:
            args.append(arg1)
        if arity > 1:
            args.append(arg2)
    b0 = b.copy()
    try:
        method(b, *args)
    except:
        # When the method call fails, b should equal b0, i.e. b is unchanged,
        # iff the method has safe precheck=True behavior by default.
        # loosebidict has precheck=False behavior by default, so this won't
        # hold for (arity == -1) bulk updates to loosebidict.
        if not loose or arity != -1:
            assert b == b0
            assert b.inv == b0.inv
    assert dict(b) == inv(b.inv)
    assert dict(b.inv) == inv(b)
    if ordered and methodname != 'move_to_end' and (
            (not loose or arity != -1)):
        items0 = list(viewitems(b0))
        items1 = list(viewitems(b))
        common = set(items0) & set(items1)
        for i in common:
            idx0 = items0.index(i)
            idx1 = items1.index(i)
            beforei0 = [j for j in items0[:idx0] if j in common]
            beforei1 = [j for j in items1[:idx1] if j in common]
            assert beforei0 == beforei1
            afteri0 = [j for j in items0[idx0 + 1:] if j in common]
            afteri1 = [j for j in items1[idx1 + 1:] if j in common]
            assert afteri0 == afteri1


@pytest.mark.parametrize('B', mutable_bidict_types)
@pytest.mark.parametrize('on_dup_key', ondupbehaviors)
@pytest.mark.parametrize('on_dup_val', ondupbehaviors)
@pytest.mark.parametrize('on_dup_kv', ondupbehaviors)
@given(d=d, items=itemlists)
def test_putall_precheck_true(B, on_dup_key, on_dup_val, on_dup_kv, d, items):
    b = B(d)
    b0 = b.copy()
    before = viewitems(b0)
    new = list(iteritems(items) if isinstance(items, Mapping) else items)
    newset = frozenset(new)
    newk = [k for (k, v) in newset]
    newv = [v for (k, v) in newset]
    try:
        b.putall(items, on_dup_key=on_dup_key, on_dup_val=on_dup_val, on_dup_kv=on_dup_kv,
                 precheck=True)
    except KeyAndValueNotUniqueError as e:
        assert on_dup_kv is RAISE
        (k1, v1), (k2, v2) = e.args
        assert (((k1, v1) in before and (k2, v2) in before) or
                ((k1, v1) in newset and (k2, v2) in newset))
    except KeyNotUniqueError as e:
        assert on_dup_key is RAISE
        (k0, v0) = e.args[0]
        vs = [v for (k, v) in new if k == k0]
        assert (k0 in b0 and all(b0[k0] != v for v in vs)) or newk.count(k0) > 1
    except ValueNotUniqueError as e:
        assert on_dup_val is RAISE
        (k0, v0) = e.args[0]
        ks = [k for (k, v) in new if v == v0]
        assert (v0 in b0.inv and all(b0.inv[v0] != k for k in ks)) or newv.count(v0) > 1
    else:
        newdd = OrderedDict(_dedup_update(on_dup_key, on_dup_val, on_dup_kv, items))
        discarded = [i for i in new if i not in viewitems(newdd)]
        for (k, v) in discarded:
            assert newk.count(k) > 1 or newv.count(v) > 1
        after = viewitems(b)
        missing = object()
        for (k, v) in iteritems(newdd):
            oldv = b0.get(k, missing)
            oldk = b0.inv.get(v, missing)
            dupk = oldv is not missing
            dupv = oldk is not missing
            if (k, v) in after:
                if (k, v) in before:
                    continue
                # (k, v) was added
                if dupk and dupv:
                    assert on_dup_kv is not RAISE
                    assert (oldk, v) in before
                    assert (k, oldv) in before
                    assert (oldk, v) not in after
                    assert (k, oldv) not in after
                elif dupk:
                    assert on_dup_key is not RAISE
                    assert (k, oldv) in before
                    assert (k, oldv) not in after
                elif dupv:
                    assert on_dup_val is not RAISE
                    assert (oldk, v) in before
                    assert (oldk, v) not in after
            else:
                # (k, v) was not added
                if dupk and dupv:
                    assert on_dup_kv is not RAISE
                    assert (oldk, v) in before
                    assert (k, oldv) in before
                elif dupk:
                    assert on_dup_key is not RAISE
                    assert (k, oldv) in before
                elif dupv:
                    assert on_dup_val is not RAISE
                    assert (oldk, v) in before

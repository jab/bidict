"""
Property-based tests using https://hypothesis.readthedocs.io
"""

from bidict import (
    IGNORE, OVERWRITE, RAISE,
    bidict, loosebidict, looseorderedbidict, orderedbidict,
    frozenbidict, frozenorderedbidict)
from bidict.compat import iteritems
from collections import OrderedDict
from hypothesis import assume, given, settings
from hypothesis.strategies import integers, lists, tuples
from os import getenv
import pytest


# https://groups.google.com/d/msg/hypothesis-users/8FVs--1yUl4/JEkJ02euEwAJ
settings.register_profile('default', settings(strict=True))
settings.load_profile(getenv('HYPOTHESIS_PROFILE', 'default'))


def to_inv_odict(items):
    return OrderedDict((v, k) for (k, v) in items)


def dedup(items):
    pruned = list(iteritems(to_inv_odict(iteritems(to_inv_odict(items)))))
    assume(len(pruned) >= len(items) // 2)
    return pruned


ondupbehaviors = (IGNORE, OVERWRITE, RAISE)
mutable_bidict_types = (bidict, loosebidict, looseorderedbidict, orderedbidict)
bidict_types = mutable_bidict_types + (frozenbidict, frozenorderedbidict)
mutating_methods_by_arity = {
    0: ('clear', 'popitem'),
    1: ('__delitem__', 'pop', 'setdefault', 'move_to_end'),
    2: ('__setitem__', 'pop', 'put', 'forceput', 'setdefault'),
    -1: ('update', 'forceupdate'),
}
immutable = integers()
itemlists = lists(tuples(immutable, immutable))
inititems = itemlists.map(dedup)


@pytest.mark.parametrize('B', bidict_types)
@given(init=inititems)
def test_equality(B, init):
    b = B(init)
    d = dict(init)
    o = OrderedDict(init)
    oi = to_inv_odict(iteritems(o))
    di = OrderedDict(oi)
    assert b == d
    assert b == o
    assert not b != d
    assert not b != o
    assert b.inv == oi
    assert b.inv == di
    assert not b.inv != oi
    assert not b.inv != di


@pytest.mark.parametrize('B', bidict_types)
@given(init=inititems)
def test_bidirectional_mappings(B, init):
    ordered = hasattr(B, '__reversed__')
    C = list if ordered else sorted
    b = B(init)
    keysf = C(k for (k, v) in iteritems(b))
    keysi = C(b.inv[v] for (k, v) in iteritems(b))
    assert keysf == keysi
    valsf = C(b[k] for (v, k) in iteritems(b.inv))
    valsi = C(v for (v, k) in iteritems(b.inv))
    assert valsf == valsi


@pytest.mark.parametrize('arity, methodname',
    [(a, m) for (a, ms) in iteritems(mutating_methods_by_arity) for m in ms])
@pytest.mark.parametrize('B', mutable_bidict_types)
@given(init=inititems, arg1=immutable, arg2=immutable, items=itemlists)
def test_consistency_after_mutation(arity, methodname, B, init, arg1, arg2, items):
    method = getattr(B, methodname, None)
    if not method:
        return
    args = []
    if arity == -1:
        args.append(items)
    else:
        if arity > 0:
            args.append(arg1)
        if arity > 1:
            args.append(arg2)
    b0 = B(init)
    b1 = b0.copy()
    try:
        method(b1, *args)
    except:
        # All methods should fail clean.
        assert b1 == b0
        assert b1.inv == b0.inv
        return
    # Method succeeded -> b1 should pass consistency checks.
    assert b1 == to_inv_odict(iteritems(b1.inv))
    assert b1.inv == to_inv_odict(iteritems(b1))


@pytest.mark.parametrize('B', mutable_bidict_types)
@pytest.mark.parametrize('on_dup_key', ondupbehaviors)
@pytest.mark.parametrize('on_dup_val', ondupbehaviors)
@pytest.mark.parametrize('on_dup_kv', ondupbehaviors)
@given(init=inititems, items=itemlists)
def test_putall(B, on_dup_key, on_dup_val, on_dup_kv, init, items):
    b0 = B(init)
    expect = b0.copy()
    expectexc = None
    for (k, v) in items:
        try:
            expect.put(k, v, on_dup_key=on_dup_key, on_dup_val=on_dup_val, on_dup_kv=on_dup_kv)
        except Exception as e:
            expectexc = e
            expect = b0  # bulk updates fail clean
            break
    check = b0.copy()
    checkexc = None
    try:
        check.putall(items, on_dup_key=on_dup_key, on_dup_val=on_dup_val, on_dup_kv=on_dup_kv)
    except Exception as e:
        checkexc = e
    assert type(checkexc) == type(expectexc)
    assert check == expect
    assert check.inv == expect.inv

"""
Property-based tests using https://warehouse.python.org/project/hypothesis/
"""

from bidict import (
    OrderedBidirectionalMapping, IGNORE, OVERWRITE, RAISE,
    KeyNotUniqueError, ValueNotUniqueError, KeyAndValueNotUniqueError,
    bidict, loosebidict, looseorderedbidict, orderedbidict)
from bidict.compat import iteritems, viewitems
from collections import Mapping
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

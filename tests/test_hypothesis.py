"""
Property-based tests using https://warehouse.python.org/project/hypothesis/
"""

from bidict import (bidict, loosebidict, looseorderedbidict, orderedbidict,
                    frozenbidict, frozenorderedbidict,
                    OrderedBidirectionalMapping)
from bidict.compat import iteritems, viewitems
from hypothesis import assume, given, settings
from hypothesis.strategies import (
    binary, booleans, dictionaries, floats, frozensets, integers,
    lists, none, recursive, text, tuples)
from math import isnan
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


def isnan_(x):
    return isinstance(x, float) and isnan(x)


def both_nan(a, b):
    return isnan_(a) and isnan_(b)


def eq_nan(a, b):
    return a == b or both_nan(a, b)


bidict_types = (bidict, loosebidict, looseorderedbidict, orderedbidict,
                frozenbidict, frozenorderedbidict)
mutating_methods_by_arity = {
    0: ('clear', 'popitem',),
    1: ('__delitem__', 'pop', 'setdefault', 'move_to_end',),
    2: ('__setitem__', 'pop', 'put', 'forceput', 'setdefault',),
    -1: ('update', 'forceupdate',),
    # TODO: test putall with all duplication behaviors
}
sz = dict(average_size=2)
immu_atom = none() | booleans() | integers() | floats() | text(**sz) | binary(**sz)
immu_coll = lambda e: frozensets(e, **sz) | lists(e, **sz).map(tuple)
immutable = recursive(immu_atom, immu_coll)
d = dictionaries(immutable, immutable, average_size=5).map(prune_dup_vals)


@given(d)
def test_len(d):
    b = bidict(d)
    assert len(b) == len(b.inv) == len(d)


@given(d)
def test_bidirectional_mappings(d):
    b = bidict(d)
    for k, v in iteritems(b):
        assert eq_nan(k, b.inv[v])
    for v, k in iteritems(b.inv):
        assert eq_nan(b[k], v)


@given(d)
def test_equality(d):
    assume(not any(isnan_(k) or isnan_(v) for (k, v) in iteritems(d)))
    i = inv(d)
    b = bidict(d)
    assert b == d
    assert b.inv == i
    assert not b != d
    assert not b.inv != i


@pytest.mark.parametrize('arity,methodname',
    [(a, m) for (a, ms) in iteritems(mutating_methods_by_arity) for m in ms])
@pytest.mark.parametrize('B', bidict_types)
@given(d=d, arg1=immutable, arg2=immutable, itemlist=lists(tuples(immutable, immutable), **sz))
def test_consistency(arity, methodname, B, d, arg1, arg2, itemlist):
    assume(not any(isnan_(k) or isnan_(v) for (k, v) in iteritems(d)))
    b = B(d)
    assert dict(b) == inv(b.inv)
    assert dict(b.inv) == inv(b)
    method = getattr(B, methodname, None)
    if not method:
        return
    args = []
    # The assume calls below tell hypothesis to not waste time exploring
    # different values of args that aren't used with the current arity,
    # leaving more time to explore interesting values of args that are used.
    if arity == -1:
        assume(arg1 is None and arg2 is None)
        args.append(itemlist)
    else:
        assume(not itemlist)
        assume((arity > 0 or arg1 is None) and (arity > 1 or arg2 is None))
        if arity > 0:
            args.append(arg1)
        if arity > 1:
            args.append(arg2)
    b0 = b.copy()
    try:
        method(b, *args)
    except:
        # When the method call fails, b should equal b0, i.e. b is unchanged.
        # This should hold even for bulk updates since they're atomic.
        assert b == b0
        assert b.inv == b0.inv
    assert dict(b) == inv(b.inv)
    assert dict(b.inv) == inv(b)
    ordered = issubclass(B, OrderedBidirectionalMapping)
    if ordered and methodname != 'move_to_end':
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

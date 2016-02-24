"""
Property-based tests using https://warehouse.python.org/project/hypothesis/
"""

from bidict import (bidict, loosebidict, looseorderedbidict, orderedbidict,
                    frozenbidict, frozenorderedbidict,
                    OrderedBidirectionalMapping)
from bidict.compat import iteritems, viewitems
from hypothesis import assume, given, settings
from hypothesis.strategies import (
    binary, booleans, choices, dictionaries, floats, frozensets, integers,
    lists, none, recursive, text, tuples)
from math import isnan
from os import getenv


# https://groups.google.com/d/msg/hypothesis-users/8FVs--1yUl4/JEkJ02euEwAJ
settings.register_profile('default', settings(strict=True))
settings.load_profile(getenv('HYPOTHESIS_PROFILE', 'default'))


def inv(d):
    return {v: k for (k, v) in iteritems(d)}


def prune_dup_vals(d):
    pruned = inv(inv(d))
    assume(len(pruned) >= len(d) // 2)
    return pruned


def both_nan(a, b):
    return isinstance(a, float) and isinstance(b, float) and \
            isnan(a) and isnan(b)


def eq_nan(a, b):
    return a == b or both_nan(a, b)


bidict_types = (bidict, loosebidict, looseorderedbidict, orderedbidict,
                frozenbidict, frozenorderedbidict)
mutating_methods_by_arity = {
    0: ('clear', 'popitem',),
    1: ('__delitem__', 'pop', 'setdefault', 'move_to_end',),
    2: ('__setitem__', 'pop', 'put', 'forceput', 'setdefault',),
    -1: ('update', 'forceupdate',),
}
# otherwise data gen. in hypothesis>=1.19 is so slow the health checks fail:
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


# work around https://bitbucket.org/pypy/pypy/issue/1974
nan = float('nan')
WORKAROUND_NAN_BUG = (nan, nan) != (nan, nan)


@given(d)
def test_equality(d):
    if WORKAROUND_NAN_BUG:
        assume(nan not in d)
    i = inv(d)
    if WORKAROUND_NAN_BUG:
        assume(nan not in i)
    b = bidict(d)
    assert b == d
    assert b.inv == i
    assert not b != d
    assert not b.inv != i


sz['average_size'] = 2

@given(d, immutable, immutable, lists(tuples(immutable, immutable), **sz))
def test_consistency(d, arg1, arg2, itemlist):
    for B in bidict_types:
        ordered = issubclass(B, OrderedBidirectionalMapping)
        b0 = B(d)
        assert dict(b0) == inv(b0.inv)
        assert dict(b0.inv) == inv(b0)
        for arity, methods in iteritems(mutating_methods_by_arity):
            for methodname in methods:
                method = getattr(B, methodname, None)
                if not method:
                    continue
                b = B(b0)
                if ordered:
                    items0 = list(viewitems(b))
                args = []
                if arity == -1:
                    args.append(itemlist)
                if arity > 0:
                    args.append(arg1)
                if arity > 1:
                    args.append(arg2)
                try:
                    method(b, *args)
                except:
                    pass
                assert dict(b) == inv(b.inv)
                assert dict(b.inv) == inv(b)
                if ordered and methodname != 'move_to_end':
                    items1 = list(viewitems(b))
                    common = set(items0) & set(items1)
                    for i in common:
                        idx0 = items0.index(i)
                        idx1 = items1.index(i)
                        beforei0 = [j for j in items0[:idx0] if j in common]
                        beforei1 = [j for j in items1[:idx1] if j in common]
                        assert beforei0 == beforei1
                        afteri0 = [j for j in items0[idx0+1:] if j in common]
                        afteri1 = [j for j in items1[idx1+1:] if j in common]
                        assert afteri0 == afteri1

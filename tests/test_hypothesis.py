"""
Property-based tests using https://warehouse.python.org/project/hypothesis/
"""

from bidict import (bidict, loosebidict, looseorderedbidict, orderedbidict,
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


mutable_bidict_types = (bidict, loosebidict, looseorderedbidict, orderedbidict)
mutating_methods_by_arity = {
    0: ('clear', 'popitem',),
    1: ('__delitem__', 'pop', 'setdefault', 'move_to_end',),
    2: ('__setitem__', 'pop', 'put', 'forceput', 'setdefault',),
    -1: ('update', 'forceupdate',),
}
# otherwise data gen. in hypothesis>=1.19 is so slow the health checks fail:
kw = dict(average_size=2)
immu_atom = none() | booleans() | integers() | floats() | text(**kw) | binary(**kw)
immu_coll = lambda e: frozensets(e, **kw) | lists(e, **kw).map(tuple)
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


@given(d, immutable, immutable, lists(tuples(immutable, immutable)))
def test_consistency_after_mutation(d, arg1, arg2, itemlist):
    for arity, mms in iteritems(mutating_methods_by_arity):
        for B in mutable_bidict_types:
            ordered = issubclass(B, OrderedBidirectionalMapping)
            for mname in mms:
                mm = getattr(B, mname, None)
                if not mm:
                    continue
                b = B(d)
                args = []
                if arity > 0:
                    args.append(arg1)
                if arity > 1:
                    args.append(arg2)
                if arity == -1:  # update and forceupdate
                    args.append(itemlist)
                assert dict(b) == inv(b.inv)
                assert dict(b.inv) == inv(b)
                if ordered:
                    items1 = list(viewitems(b))
                try:
                    mm(b, *args)
                except:
                    pass
                assert dict(b) == inv(b.inv)
                assert dict(b.inv) == inv(b)
                if ordered and mname != 'move_to_end':
                    items2 = list(viewitems(b))
                    common = set(items1) & set(items2)
                    for i in common:
                        idx1 = items1.index(i)
                        idx2 = items2.index(i)
                        beforei1 = [j for j in items1[:idx1] if j in common]
                        beforei2 = [j for j in items2[:idx2] if j in common]
                        assert beforei1 == beforei2
                        afteri1 = [j for j in items1[idx1+1:] if j in common]
                        afteri2 = [j for j in items2[idx2+1:] if j in common]
                        assert afteri1 == afteri2

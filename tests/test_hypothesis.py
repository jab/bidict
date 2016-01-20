"""
Property-based tests using https://warehouse.python.org/project/hypothesis/
"""

from bidict import bidict, orderedbidict
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
    return {v: k for (k, v) in d.items()}


def prune_dup_vals(d):
    pruned = inv(inv(d))
    assume(len(pruned) >= len(d) // 2)
    return pruned


def both_nan(a, b):
    return isinstance(a, float) and isinstance(b, float) and \
            isnan(a) and isnan(b)


def eq_nan(a, b):
    return a == b or both_nan(a, b)


mutating_methods_by_arity = {
    0: (bidict.clear, bidict.popitem, orderedbidict.popitem,),
    1: (bidict.__delitem__, bidict.pop, bidict.setdefault,
        orderedbidict.move_to_end,),
    2: (bidict.__setitem__, bidict.pop, bidict.put, bidict.forceput,
        bidict.setdefault,),
    -1: (bidict.update, bidict.forceupdate,),
}
# otherwise data gen. in hypothesis>=1.19 is so slow the health checks fail:
kw = dict(average_size=2)
immu_atom = none() | booleans() | integers() | floats() | text(**kw) | binary(**kw)
immu_coll = lambda e: frozensets(e, **kw) | lists(e, **kw).map(tuple)
immutable = recursive(immu_atom, immu_coll)
d = dictionaries(immutable, immutable, **kw).map(prune_dup_vals)


@given(d)
def test_len(d):
    b = bidict(d)
    assert len(b) == len(b.inv) == len(d)


@given(d)
def test_bidirectional_mappings(d):
    b = bidict(d)
    for k, v in b.items():
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


@given(d, immutable, lists(tuples(immutable, immutable)))
def test_consistency_after_mutation(d, arg, itemlist):
    for arity, mms in mutating_methods_by_arity.items():
        for mm in mms:
            b = orderedbidict(d) if 'orderedbidict' in repr(mm) else bidict(d)
            args = []
            if arity > 0:
                args.append(arg)
            if arity > 1:
                args.append(arg)
            if arity == -1:  # update and forceupdate
                args.append(itemlist)
            assert b == inv(b.inv)
            assert b.inv == inv(b)
            try:
                mm(b, *args)
            except:
                pass
            assert b == inv(b.inv)
            assert b.inv == inv(b)

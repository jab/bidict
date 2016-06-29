"""
Property-based tests using https://warehouse.python.org/project/hypothesis/
"""

from bidict import (
    OrderedBidirectionalMapping, IGNORE, OVERWRITE, RAISE,
    bidict, loosebidict, looseorderedbidict, orderedbidict,
    frozenbidict, frozenorderedbidict)
from bidict.compat import iteritems, viewitems
from collections import OrderedDict
from hypothesis import given, settings
from hypothesis.strategies import integers, lists, tuples
from os import getenv
import pytest


# https://groups.google.com/d/msg/hypothesis-users/8FVs--1yUl4/JEkJ02euEwAJ
settings.register_profile('default', settings(strict=True))
settings.load_profile(getenv('HYPOTHESIS_PROFILE', 'default'))


def to_inv_odict(items):
    return OrderedDict((v, k) for (k, v) in items)


def prune_dup_vals(items):
    return list(iteritems(to_inv_odict(iteritems(to_inv_odict(items)))))


ondupbehaviors = (IGNORE, OVERWRITE, RAISE)
mutable_bidict_types = (bidict, loosebidict, looseorderedbidict, orderedbidict)
bidict_types = mutable_bidict_types + (frozenbidict, frozenorderedbidict)
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
inititems = itemlists.map(prune_dup_vals)


@pytest.mark.parametrize('B', bidict_types)
@given(init=inititems)
def test_equality(B, init):
    b = B(init)
    d = OrderedDict(init)
    assert b == d
    assert not b != d
    i = to_inv_odict(iteritems(d))
    assert b.inv == i
    assert not b.inv != i


@pytest.mark.parametrize('B', bidict_types)
@given(init=inititems)
def test_bidirectional_mappings(B, init):
    ordered = issubclass(B, OrderedBidirectionalMapping)
    C = list if ordered else sorted
    b = B(init)
    keysf = C(k for (k, v) in iteritems(b))
    keysi = C(b.inv[v] for (k, v) in iteritems(b))
    assert keysf == keysi
    valsf = C(b[k] for (v, k) in iteritems(b.inv))
    valsi = C(v for (v, k) in iteritems(b.inv))
    assert valsf == valsi


@pytest.mark.parametrize('arity,methodname',
    [(a, m) for (a, ms) in iteritems(mutating_methods_by_arity) for m in ms])
@pytest.mark.parametrize('B', mutable_bidict_types)
@given(init=inititems, arg1=immutable, arg2=immutable, items=itemlists)
def test_consistency_after_mutation(arity, methodname, B, init, arg1, arg2, items):
    method = getattr(B, methodname, None)
    if not method:
        return
    b = B(init)
    args = []
    if arity == -1:
        args.append(items)
    else:
        if arity > 0:
            args.append(arg1)
        if arity > 1:
            args.append(arg2)
    b0 = b.copy()
    try:
        method(b, *args)
    except:
        # All methods should fail clean, reverting any changes made before failure.
        assert b == b0
        assert b.inv == b0.inv
    else:
        assert b == to_inv_odict(iteritems(b.inv))
        assert b.inv == to_inv_odict(iteritems(b))

        # If b is an orderedbidict and the method is not expected to change the
        # ordering, test that the relative ordering of any items that survived
        # the mutation is preserved, i.e. if (k1, v1) came before (k2, v2)
        # before the mutation, it still does after.
        #
        # In the case of forceupdate(), order is preserved as much as possible,
        # but in some cases it is not preserved completely, e.g.::
        #
        #     >>> o = orderedbidict([(0, 2), (2, 1)])
        #     >>> o.forceupdate([(1, 2), (0, 0), (0, 2)])
        #     >>> o
        #     orderedbidict([(2, 1), (0, 2)])
        #
        # So this test is skipped for forceupdate().
        ordered = issubclass(B, OrderedBidirectionalMapping)
        if ordered and methodname not in ('move_to_end', 'forceupdate'):
            items0 = viewitems(b0)
            items1 = viewitems(b)
            common = items0 & items1
            if common:
                items0 = list(items0)
                items1 = list(items1)
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

"""
Property-based tests using https://warehouse.python.org/project/hypothesis/
"""


from hypothesis import assume, given
from hypothesis.strategies import (
    binary, booleans, choices, dictionaries, floats, frozensets, integers,
    lists, none, one_of, text, recursive)

from bidict import bidict, frozenbidict
from bidict.util import both_nan


def inv(d):
    return {v: k for (k, v) in d.items()}


def prune_dup_vals(d):
    pruned = inv(inv(d))
    assume(len(pruned) >= len(d) // 2)
    return pruned


mutating_methods_by_arity = {
    0: (bidict.clear, bidict.popitem,),
    1: (bidict.__delitem__, bidict.pop, bidict.setdefault,),
    2: (bidict.__setitem__, bidict.pop, bidict.put, bidict.forceput,
        bidict.setdefault,),
    -1: (bidict.update, bidict.forceupdate,),
}
immutable_types = recursive(
    one_of(none(), booleans(), integers(), floats(), text(), binary()),
    lambda elts: one_of(frozensets(elts), lists(elts).map(tuple)))
d = dictionaries(immutable_types, immutable_types).map(prune_dup_vals)


@given(d)
def test_len(d):
    assert len(d) == len(inv(d)) == len(bidict(d))


@given(d)
def test_bidirectional_mappings(d):
    b = bidict(d)
    for k, v in b.items():
        v_ = b[k]
        k_ = b.inv[v]
        assert k == k_ or both_nan(k, k_)
        assert v == v_ or both_nan(v, v_)


@given(d)
def test_inv_identity(d):
    b = bidict(d)
    assert b is b.inv.inv
    assert b.inv is b.inv.inv.inv


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


@given(d, choice=choices())
def test_consistency_after_mutation(d, choice):
    assume(d)
    for arity, mms in mutating_methods_by_arity.items():
        for mm in mms:
            for existing_key in (True, False):
                for existing_val in (True, False):
                    b = bidict(d)
                    K = list(b.keys())
                    V = list(b.values())
                    args = []
                    if arity > 0:
                        args.append(choice(K) if existing_key else object())
                    if arity > 1:
                        args.append(choice(V) if existing_val else object())
                    if arity == -1:  # update and forceupdate
                        l = []
                        for i in range(32):
                            k = choice(K) if choice((0, 1)) else object()
                            v = choice(V) if choice((0, 1)) else object()
                            l.append((k, v))
                        args.append(l)
                    assert b == inv(b.inv)
                    assert b.inv == inv(b)
                    try:
                        mm(b, *args)
                    except:
                        pass
                    assert b == inv(b.inv)
                    assert b.inv == inv(b)


@given(d)
def test_frozenbidict_hash(d):
    f = frozenbidict(d)
    assert hash(f)

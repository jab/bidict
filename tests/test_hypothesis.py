"""
Property-based tests using https://warehouse.python.org/project/hypothesis/
"""

from math import isnan

from hypothesis import assume, given
from hypothesis.strategies import (
    binary, booleans, dictionaries, floats, frozensets, integers, lists, none,
    one_of, text, recursive)

from bidict import bidict, frozenbidict


def inv(d):
    return {v: k for (k, v) in d.items()}


def prune_dup_vals(d):
    pruned = inv(inv(d))
    assume(len(pruned) >= len(d) // 2)
    return pruned


immutable_types = recursive(
    one_of(none(), booleans(), integers(), floats(), text(), binary()),
    lambda elts: one_of(frozensets(elts), lists(elts).map(tuple)))
d = dictionaries(immutable_types, immutable_types).map(prune_dup_vals)


@given(d)
def test_len(d):
    assert len(d) == len(inv(d)) == len(bidict(d))


def _isnan(x):
    return isnan(x) if isinstance(x, float) else False


def _both_nan(a, b):
    return _isnan(a) and _isnan(b)


@given(d)
def test_bidirectional_mappings(d):
    b = bidict(d)
    for k, v in b.items():
        v_ = b[k]
        k_ = b.inv[v]
        assert k == k_ or _both_nan(k, k_)
        assert v == v_ or _both_nan(v, v_)


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


@given(d)
def test_frozenbidict_hash(d):
    f = frozenbidict(d)
    assert hash(f)

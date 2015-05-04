"""
Property-based tests using https://warehouse.python.org/project/hypothesis/
"""

import pytest

from functools import reduce
from math import isnan
from operator import or_

from hypothesis import assume, given, strategy
from hypothesis.specifiers import dictionary

from bidict import bidict


def inv(d):
    return {v: k for (k, v) in d.items()}

def prune_dup_vals(d):
    pruned = inv(inv(d))
    assume(len(pruned) >= 0.5 * len(d))
    return pruned

immutable_types_ = (None, bool, int, float, str, bytes, tuple(), frozenset())
immutable_types = reduce(or_, map(strategy, immutable_types_))
d = strategy(dictionary(immutable_types, immutable_types)).map(prune_dup_vals)

@given(d)
def test_len(d):
    assert len(d) == len(inv(d)) == len(bidict(d))

def isnan_(x):
    return isnan(x) if isinstance(x, float) else False

def both_nan(a, b):
    return isnan_(a) and isnan_(b)

@given(d)
def test_bidirectional_mappings(d):
    b = bidict(d)
    for k, v in b.items():
        v_ = b[k]
        k_ = b.inv[v]
        assert k == k_ or both_nan(k, k_)
        assert v == v_ or both_nan(v, v_)

@given(d)
def test_getitem_with_slice(d):
    b = bidict(d)
    for k, v in b.items():
        # https://bidict.readthedocs.org/en/latest/caveats.html#none-breaks-the-slice-syntax
        if v is not None:
            k_ = b[:v]
            assert k == k_ or both_nan(k, k_)
        if k is not None:
            v_ = b.inv[:k]
            assert v == v_ or both_nan(v, v_)

@given(d)
def test_inv_identity(d):
    b = bidict(d)
    assert b is b.inv.inv is ~~b
    assert b.inv is b.inv.inv.inv is ~b

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
    assert ~b == i
    assert not b != d
    assert not ~b != i

"""
Property-based tests using https://warehouse.python.org/project/hypothesis/
"""

from math import isnan

from hypothesis import assume, given, strategy
from hypothesis.specifiers import dictionary

from bidict import bidict


def safe_isnan(x):
    return isnan(x) if isinstance(x, float) else False

immutable_types = (
    strategy(int) | strategy(float) | strategy(str) |
    strategy(bool))

@given(dictionary(immutable_types, immutable_types))
def test_basic_properties_bidict(fwd):

    assume(all(
        not safe_isnan(x) for kv in fwd.items() for x in kv
    ))

    # ensure all values in fwd are unique
    assume(len(fwd.values()) == len(set(fwd.values())))

    inv = {v: k for (k, v) in fwd.items()}
    b = bidict(fwd)

    # len
    assert len(fwd) == len(inv) == len(b)

    # getitem
    for k, v in b.items():
        k_ = b[:v]
        v_ = b[k]
        assert k == k_
        assert v == v_

    # .inv, is, ==, !=, and ~ operators. == and != are polymorphic.
    assert b is b.inv.inv is ~~b
    assert b.inv is b.inv.inv.inv is ~b
    assert b == fwd or BUGGY_PYPY
    assert ~b == inv or BUGGY_PYPY
    assert not b != fwd or BUGGY_PYPY
    assert not ~b != inv or BUGGY_PYPY

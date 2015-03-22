"""
Property-based tests using https://warehouse.python.org/project/hypothesis/
"""

from functools import reduce
from math import isnan
from operator import or_

from hypothesis import assume, given, strategy
from hypothesis.specifiers import dictionary

from bidict import bidict

def safe_isnan(x):
    return isnan(x) if isinstance(x, float) else False

# work around https://bitbucket.org/pypy/pypy/issue/1974
nan = float('nan')
WORKAROUND_NAN_BUG = (nan, nan) != (nan, nan)
if WORKAROUND_NAN_BUG:
    from warnings import warn
    warn('working around buggy python implementation: '
         '(nan, nan) should equal (nan, nan)')

immutable_types_ = (None, bool, int, float, str, bytes, tuple(), frozenset())
immutable_types = reduce(or_, map(strategy, immutable_types_))

@given(dictionary(immutable_types, immutable_types))
def test_basic_properties_bidict(fwd):
    # ensure all values in fwd are unique
    assume(len(fwd.values()) == len(set(fwd.values())))

    inv = {v: k for (k, v) in fwd.items()}
    b = bidict(fwd)

    # len
    assert len(fwd) == len(inv) == len(b)

    # getitem
    for k, v in b.items():
        k_ = b[:v] if v is not None else b.inv[v]
        v_ = b[k]
        assert k == k_ if not safe_isnan(k) else safe_isnan(k_)
        assert v == v_ if not safe_isnan(v) else safe_isnan(v_)

    # .inv, is, ==, !=, and ~ operators. == and != are polymorphic.
    assert b is b.inv.inv is ~~b
    assert b.inv is b.inv.inv.inv is ~b
    assert b == fwd or WORKAROUND_NAN_BUG
    assert ~b == inv or WORKAROUND_NAN_BUG
    assert not b != fwd or WORKAROUND_NAN_BUG
    assert not ~b != inv or WORKAROUND_NAN_BUG

"""
Property-based tests using https://warehouse.python.org/project/hypothesis/
"""

from bidict import bidict
from hypothesis import assume, given
from hypothesis.specifiers import dictionary
from math import isnan

# work around https://bitbucket.org/pypy/pypy/issue/1974
nan = float('nan')
BUGGY_PYPY = (nan, nan) != (nan, nan)
if BUGGY_PYPY:
    from warnings import warn
    warn('working around buggy pypy')

@given(dictionary(float, float))
def test_basic_properties_bidict(fwd):

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
        assert k == k_ if not isnan(k) else isnan(k_)
        assert v == v_ if not isnan(v) else isnan(v_)

    # .inv, is, ==, !=, and ~ operators. == and != are polymorphic.
    assert b is b.inv.inv is ~~b
    assert b.inv is b.inv.inv.inv is ~b
    assert b == fwd or BUGGY_PYPY
    assert ~b == inv or BUGGY_PYPY
    assert not b != fwd or BUGGY_PYPY
    assert not ~b != inv or BUGGY_PYPY

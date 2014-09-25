# test_large_lists.py
# David Prager Branner
# 20140925

"""Supply tests with large lists of randomly constructed items."""

import bidict as B
import pytest
import random
import string

def random_ints(cardinality=10, hi=10, lo=-10):
    """return list of `cardinality` ints, each in range (lo, hi)."""
    if cardinality > hi - lo:
        raise Exception(
                'cardinality ({}) > hi - lo ({}); impossible condition'.
                format(cardinality, hi-lo))
    results = set()
    while len(results) < cardinality:
        results.add( random.randint(lo, hi))
    return list(results)

def random_strings(length=10, cardinality=10):
    """return list of `cardinality` strings, each length `length`."""
    results = set()
    while len(results) < cardinality:
        results.add(''.join(
                random.choice(string.ascii_letters + string.digits)
                for i in range(length)))
    return list(results)

hi_lo = 10000000
card = 100000
ints_to_strs = [(i) for i in zip(
    random_ints(card, hi_lo, -hi_lo),
    random_strings(10, card))]
strs_to_ints = [(i) for i in zip(
    random_strings(10, card),
    random_ints(card, hi_lo, -hi_lo))]

def test_inverse_01(lst=ints_to_strs):
    assert lst == list(B.inverted(B.inverted(lst)))

def test_inverse_02(lst=strs_to_ints):
    assert lst == list(B.inverted(B.inverted(lst)))

def test_get_item_01(lst=ints_to_strs):
    b = B.bidict(lst)
    for i in range(card//1000):
        r = random.choice(list(b.keys()))
        assert r == b[:b[r]]

def test_get_item_02(lst=strs_to_ints):
    b = B.bidict(lst)
    for i in range(card//1000):
        r = random.choice(list(b.keys()))
        assert r == b[:b[r]]

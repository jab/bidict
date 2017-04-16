#! /usr/bin/env python
# time_manual_reverse_dict.py
# David Prager Branner
# 20140925

import bidict as B
import time
import random
import string


def main(trials=10, card=100000, hi_lo = 10000000):
    # Example with int: str
    total_time_bidict = 0
    total_time_revdict = 0
    for i in range(trials):
        start_time = time.time()
        ints_to_strs = construct_ints_to_strs(card, hi_lo)
        b = B.bidict(ints_to_strs)
        total_time_bidict += time.time() - start_time
        start_time = time.time()
        rev = {v: k for k, v in ints_to_strs}
        total_time_revdict += time.time() - start_time
    print('Example with int: str.')
    print('''In {} trials, average time for a list of cardinality {}:\n'''
            '''    bidict:        {:.4f} sec.\n'''
            '''    reversed dict: {:.4f} sec.'''.
            format(trials, card, total_time_bidict/trials,
                total_time_revdict/trials))
    # Example with str: int
    total_time_bidict = 0
    total_time_revdict = 0
    for i in range(trials):
        start_time = time.time()
        strs_to_ints = construct_strs_to_ints(card, hi_lo)
        b = B.bidict(strs_to_ints)
        total_time_bidict += time.time() - start_time
        start_time = time.time()
        rev = {v: k for k, v in ints_to_strs}
        total_time_revdict += time.time() - start_time
    print('\nExample with str: int.')
    print('''In {} trials, average time for a list of cardinality {}:\n'''
            '''    bidict:        {:.4f} sec.\n'''
            '''    reversed dict: {:.4f} sec.'''.
            format(trials, card, total_time_bidict/trials,
                total_time_revdict/trials))

def construct_ints_to_strs(card, hi_lo):
    return [(i) for i in zip(
            random_ints(card, hi_lo, -hi_lo),
                random_strings(10, card))]

def construct_strs_to_ints(card, hi_lo):
    return [(i) for i in zip(
            random_strings(10, card),
                random_ints(card, hi_lo, -hi_lo))]

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


from bidict import bidict
from bidict.compat import iteritems, viewvalues
from itertools import islice
from random import choice
import pytest


n = 1024
# TODO: test with other sizes? putting the below inside a for loop doesn't work
d = {object(): object() for _ in range(n)}

group = 'init_%s' % n
@pytest.mark.benchmark(group=group)
def test_bidict_init(benchmark):
    benchmark(bidict, d)

def invdict(d, _missing=object()):
    inv = {}
    for (k, v) in iteritems(d):
        if v in inv:
            raise Exception('Duplicate value')
        inv[v] = k
    return inv

@pytest.mark.benchmark(group=group)
def test_invdict_init(benchmark):
    benchmark(invdict, d)


group = 'setitem_%s' % n
# TODO: test with some value-overwriting __setitem__ calls?
@pytest.mark.benchmark(group=group)
def test_bidict_setitem(benchmark):
    b = bidict(d)
    @benchmark
    def setitem():
        b[object()] = object()

def setitem(d, inv, _missing=object()):
    k, v = object(), object()
    if v in inv:
        raise Exception('Value exists')
    oldval = d.get(k, _missing)
    d[k] = v
    if oldval is not _missing:
        del inv[oldval]
    inv[v] = k

@pytest.mark.benchmark(group=group)
def test_invdict_setitem(benchmark):
    inv = invdict(d)
    benchmark(setitem, d, inv)


group = 'get_key_by_val_%s' % n
randvalsubsetsize = 10  # TODO: is this a good way to do this test?
@pytest.mark.benchmark(group=group)
def test_bidict_get_key_by_val(benchmark):
    b = bidict(d)
    somevals = list(islice(viewvalues(b), randvalsubsetsize))
    benchmark(lambda: b.inv[choice(somevals)])

@pytest.mark.benchmark(group=group)
def test_invdict_get_key_by_val(benchmark):
    inv = invdict(d)
    somevals = list(islice(viewvalues(d), randvalsubsetsize))
    benchmark(lambda: inv[choice(somevals)])

"""
Benchmarks to compare performing various tasks using a bidict
against manually keeping two inverse dicts ("2idict") consistent.
"""

from bidict import bidict
from bidict.compat import iteritems, itervalues, viewkeys, viewvalues
from itertools import islice, product
from operator import attrgetter, itemgetter
from random import choice, randint
import pytest


try:
    range = xrange
except NameError:
    pass


def invdict(d, _missing=object()):
    inv = {}
    for (k, v) in iteritems(d):
        if v in inv:
            raise Exception('Duplicate value')
        inv[v] = k
    return inv


SIZES = [randint(2**x, 2**(x+1)) for x in range(5, 12, 3)]
@pytest.fixture(params=SIZES, ids=str)
def data(request):
    return {object(): object() for _ in range(request.param)}

@pytest.fixture(params=(bidict, invdict), ids=('bidict', '2idict'))
def constructor(request):
    return request.param

### benchmark 1: compare initializing a bidict to initializing an inverse dict
# TODO: test with data that has values repeated?
def test_init(benchmark, constructor, data):
    benchmark(constructor, data)


### benchmark 2: compare getting a key by value in a bidict vs. an inverse dict
def test_get_key_by_val(benchmark, constructor, data):
    # TODO: is this a good way to do this test?
    val = choice(list(viewvalues(data)))
    obj = constructor(data)
    gkbv = (lambda val: obj.inv[val]) if constructor is bidict else (
            lambda val: obj[val])
    key = benchmark(gkbv, val)
    assert data[key] == val


### benchmark 3: compare setitem for a bidict vs. an inverse dict
# TODO: test with some duplicate values?
def test_setitem(benchmark, constructor, data):
    key, val, _missing = object(), object(), object()

    if constructor is bidict:
        def setup():
            return (constructor(data),), {}

        def setitem(b):
            b[key] = val

    else:
        def setup():
            return (data.copy(), constructor(data)), {}

        def setitem(d, inv):
            if val in inv:
                raise Exception('Value exists')
            oldval = d.get(key, _missing)
            d[key] = val
            if oldval is not _missing:
                del inv[oldval]
            inv[val] = key

    # TODO: iterations=100 causes: ValueError: Can't use more than 1 `iterations` with a `setup` function.
    #benchmark.pedantic(setitem, setup=setup, iterations=100)
    benchmark.pedantic(setitem, setup=setup)


### benchmark 4: compare update for a bidict vs. an inverse dict
# TODO: test with some duplicate values?
# TODO: choose number of items in update differently?
def test_update(benchmark, constructor, data):
    _missing = object()
    items = [(object(), object()) for _ in range(len(data)//2)]

    if constructor is bidict:
        def setup():
            return (constructor(data),), {}

        def update(b):
            b.update(items)

    else:
        def setup():
            return (data.copy(), constructor(data)), {}

        def update(d, inv, items=items):
            # only test with default collision behaviors
            # (key: OVERWRITE, value: RAISE)
            itemsinv = {v: k for (k, v) in items}
            if len(items) > len(itemsinv):
                raise Exception('Nonunique values')
            common_vals = viewkeys(itemsinv) & viewkeys(inv)
            if common_vals:
                raise Exception('Values exist')
            items = dict(items)
            common_keys = viewkeys(items) & viewkeys(d)
            for k in common_keys:
                del inv[d.pop(k)]
            d.update(items)
            inv.update(itemsinv)

    # TODO: iterations=100 causes: ValueError: Can't use more than 1 `iterations` with a `setup` function.
    #benchmark.pedantic(update, setup=setup, iterations=100)
    benchmark.pedantic(update, setup=setup)

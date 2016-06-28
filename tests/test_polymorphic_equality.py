import pytest
from collections import Counter, OrderedDict, defaultdict
from bidict import bidict, frozenbidict, namedbidict
from itertools import product


class dictsubclass(dict):
    pass

d = dict(H='hydrogen', He='helium')
c = Counter(d)
o = OrderedDict(d)
dd = defaultdict(int, d)
s = dictsubclass(d)

b = bidict(d)
f = frozenbidict(d)
n = namedbidict('named', 'keys', 'vals')(d)

dicts = (d, c, o, dd, s)
bidicts = (b, f, n)


@pytest.mark.parametrize('d, b', product(dicts, bidicts))
def test_eq(d, b):
    assert d == b

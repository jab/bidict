import pytest
from collections import Counter, OrderedDict, defaultdict
from bidict import bidict, frozenbidict, namedbidict
from itertools import product


d = dict(H='hydrogen', He='helium')
c = Counter(d)
o = OrderedDict(d)
dd = defaultdict(int, d)
class dictsubclass(dict): pass
s = dictsubclass(d)

b = bidict(d)
f = frozenbidict(d)
n = namedbidict('named', 'keys', 'vals')(d)

dicts = (d, c, o, dd, s)
bidicts = (b, f, n)

@pytest.mark.parametrize('d, b', product(dicts, bidicts))
def test_eq(d, b):
    assert d == b

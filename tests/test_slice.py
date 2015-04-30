import pytest
from bidict import bidict
from bidict.compat import PY2
from itertools import product


@pytest.fixture
def b():
    return bidict(H='hydrogen')

single_test_data = {'H', 'hydrogen', -1, 0, 1}
bad_start_values = single_test_data - {'H'}
bad_stop_values = single_test_data - {'hydrogen'}
pair_test_data = set(product(single_test_data, repeat=2))


def test_good_start(b):
    assert b['H'] == 'hydrogen'
    assert b['H':] == 'hydrogen'

@pytest.mark.parametrize('start', bad_start_values)
def test_bad_start(b, start):
    with pytest.raises(KeyError):
        b[start]
    with pytest.raises(KeyError):
        b[start:]

def test_good_stop(b):
    assert b[:'hydrogen'] == 'H'

@pytest.mark.parametrize('stop', bad_stop_values)
def test_stop(b, stop):
    with pytest.raises(KeyError):
        b[:stop]

@pytest.mark.parametrize('start, stop', pair_test_data)
def test_start_stop(b, start, stop):
    with pytest.raises(TypeError):
        b[start:stop]

@pytest.mark.parametrize('step', single_test_data)
def test_step(b, step):
    with pytest.raises(TypeError):
        b[::step]

def test_empty(b):
    with pytest.raises(TypeError):
        b[::]


# see ../docs/caveat-none-slice.rst.inc or
# https://bidict.readthedocs.org/en/master/caveats.html#none-breaks-the-slice-syntax
@pytest.fixture
def b_none():
    return bidict({'key': None, None: 'val'})

@pytest.mark.xfail(not PY2, reason='none-slice unsupported on Python 3')
def test_none_slice_fwd(b_none):
    assert b_none[None:] == 'val'

@pytest.mark.xfail(not PY2, reason='none-slice unsupported on Python 3')
def test_none_slice_inv(b_none):
    assert b_none[:None] == 'key'

# mutliple slices per line with none-slice unsupported
def test_multi_slice_fwd(b_none):
    with pytest.raises(TypeError):
        b_none[None:] + ['foo'][0:][0]

def test_multi_slice_inv(b_none):
    with pytest.raises(TypeError):
        b_none[:None] + ['foo'][0:][0]

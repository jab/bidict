from itertools import product

import pytest

from bidict import bidict


@pytest.fixture
def b():
    return bidict(H='hydrogen')

single_test_data = {'H', 'hydrogen', -1, 0, 1}
bad_start_values = single_test_data - {'H'}
bad_stop_values = single_test_data - {'hydrogen'}
pair_test_data = product(single_test_data, single_test_data)


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

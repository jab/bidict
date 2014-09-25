# test_docs_content.py
# David Prager Branner
# 20140924

"""Run tests mostly matching those in docstrings."""

import bidict as B
import pytest
import random
import string

def test_basic_getitem():
    element_by_symbol = B.bidict(H='hydrogen')
    element_by_symbol['H'] = 'hydrogen'
    assert element_by_symbol['H':] == 'hydrogen'
    assert element_by_symbol[:'hydrogen'] == 'H'

def test_delete():
    element_by_symbol = B.bidict(H='hydrogen')
    element_by_symbol['He':] = 'helium'
    element_by_symbol[:'lithium'] = 'Li'
    del element_by_symbol['H':]
    del element_by_symbol[:'lithium']
    assert element_by_symbol == B.bidict({'He': 'helium'})

def test_in_01():
    element_by_symbol = B.bidict(He='helium')
    assert bool('C' in element_by_symbol) == False

def test_in_02():
    element_by_symbol = B.bidict(Hg='mercury')
    assert bool('mercury' in ~element_by_symbol) == True

def test_get():
    element_by_symbol = B.bidict(He='helium')
    assert element_by_symbol.get('C', 'carbon') == 'carbon'

def test_pop_01():
    element_by_symbol = B.bidict(He='helium')
    assert element_by_symbol.pop('He') == 'helium'

def test_pop_02():
    element_by_symbol = B.bidict(He='helium')
    element_by_symbol.pop('He')
    assert element_by_symbol == B.bidict({})

def test_pop_03():
    element_by_symbol = B.bidict(Hg='mercury')
    assert (~element_by_symbol).pop('mercury') == 'Hg'

def test_update():
    element_by_symbol = B.bidict()
    element_by_symbol.update(Hg='mercury')
    assert element_by_symbol == B.bidict({'Hg': 'mercury'})

def test_unary_inverse():
    element_by_symbol = B.bidict(Hg='mercury')
    assert ~element_by_symbol == B.bidict({'mercury': 'Hg'})

def test_unhashable_list():
    with pytest.raises(TypeError):
        anagrams_by_alphagram = B.bidict(opt=['opt', 'pot', 'top'])

def test_unhashable_sublist():
    sublist = (1, 2, '3', ('r', [4]), 5)
    with pytest.raises(TypeError):
        anagrams_by_alphagram = B.bidict(sublist)

def test_hashable_tuple():
    anagrams_by_alphagram = B.bidict(opt=('opt', 'pot', 'top'))
    assert len(anagrams_by_alphagram) == 1

def test_like_value_differing_keys_01():
    nils = B.bidict(zero=0, zilch=0, zip=0)
    assert len(nils) == 1

def test_like_value_differing_keys_02():
    b = B.bidict({1: 'one', 2: 'two'})
    b[:'two'] = 1
    assert b == B.bidict({1: 'two'})

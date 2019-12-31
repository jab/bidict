# -*- coding: utf-8 -*-
# Copyright 2009-2020 Joshua Bronson. All Rights Reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Benchmarks."""

import pytest

from bidict import OrderedBidict, ValueDuplicationError, bidict


BIDICT_TYPES = (bidict, OrderedBidict)

ELEMENTS = OrderedBidict((
    ('H', 'hydrogen'), ('He', 'helium'),
    ('Li', 'lithium'), ('Be', 'beryllium'), ('B', 'boron'), ('C', 'carbon'),
    ('N', 'nitrogen'), ('O', 'oxygen'), ('F', 'fluorine'), ('Ne', 'neon'),
    ('Na', 'sodium'), ('Mg', 'magnesium'), ('Al', 'aluminum'), ('Si', 'silicon'),
    ('P', 'phosphorus'), ('S', 'sulfur'), ('Cl', 'chlorine'), ('Ar', 'argon'),
))

UPDATE_NODUP = OrderedBidict((
    ('K', 'potassium'), ('Ca', 'calcium'), ('Sc', 'Scandium'), ('Ti', 'titanium'),
    ('V', 'vanadium'), ('Cr', 'chromium'), ('Mn', 'manganese'), ('Fe', 'iron'), ('Co', 'cobalt'),
    ('Ni', 'nickel'), ('Cu', 'copper'), ('Zn', 'zinc'), ('Ga', 'gallium'), ('Ge', 'germanium'),
    ('As', 'arsenic'), ('Se', 'selenium'), ('Br', 'bromine'), ('Kr', 'krypton'), ('Rb', 'rubidium'),
    ('Sr', 'strontium'), ('Y', 'yttrium'), ('Zr', 'zirconium'), ('Nb', 'niobium'),
    ('Mo', 'molybdenum'), ('Tc', 'technetium'), ('Ru', 'ruthenium'), ('Rh', 'rhodium'),
    ('Pd', 'palladium'), ('Ag', 'silver'), ('Cd', 'cadmium'), ('In', 'indium'), ('Sn', 'tin'),
    ('Sb', 'antimony'), ('Te', 'tellurium'), ('I', 'iodine'), ('Xe', 'xenon'), ('Cs', 'cesium'),
    ('Ba', 'barium'), ('La', 'lanthanum'), ('Ce', 'cerium'), ('Pr', 'praseodymium'),
    ('Nd', 'neodymium'), ('Pm', 'promethium'), ('Sm', 'samarium'), ('Eu', 'europium'),
    ('Gd', 'gadolinium'), ('Tb', 'terbium'), ('Dy', 'dysprosium'), ('Ho', 'holmium'),
    ('Er', 'erbium'), ('Tm', 'thulium'), ('Yb', 'ytterbium'), ('Lu', 'lutetium'), ('Hf', 'hafnium'),
    ('Ta', 'tantalum'), ('W', 'tungsten'), ('Re', 'rhenium'), ('Os', 'osmium'), ('Ir', 'iridium'),
    ('Pt', 'platinum'), ('Au', 'gold'), ('Hg', 'mercury'), ('Tl', 'thallium'), ('Pb', 'lead'),
    ('Bi', 'bismuth'), ('Po', 'polonium'), ('At', 'astatine'), ('Rn', 'radon'), ('Fr', 'francium'),
    ('Ra', 'radium'), ('Ac', 'actinium'), ('Th', 'thorium'), ('Pa', 'protactinium'),
    ('U', 'uranium'), ('Np', 'neptunium'), ('Pu', 'plutonium'), ('Am', 'americium'),
    ('Cm', 'curium'), ('Bk', 'berkelium'), ('Cf', 'californium'), ('Es', 'einsteinium'),
    ('Fm', 'fermium'), ('Md', 'mendelevium'), ('No', 'nobelium'), ('Lr', 'lawrencium'),
    ('Rf', 'rutherfordium'), ('Db', 'dubnium'), ('Sg', 'seaborgium'), ('Bh', 'bohrium'),
    ('Hs', 'hassium'), ('Mt', 'meitnerium'), ('Ds', 'darmstadtium'), ('Rg', 'roentgenium'),
    ('Cn', 'copernicium'),
))

UPDATE_WITHDUPVAL = OrderedBidict(UPDATE_NODUP, key_with_dup_val='hydrogen')


@pytest.mark.parametrize('bi_cls', BIDICT_TYPES)
def test_put_nodup(bi_cls, benchmark):
    """Test inserting a new item with no key or value duplication using put."""
    some_bidict = bi_cls(ELEMENTS)
    benchmark(some_bidict.put, 'K', 'potassium')


@pytest.mark.parametrize('bi_cls', BIDICT_TYPES)
def test_put_withdup(bi_cls, benchmark):
    """Test inserting a new item with a duplicate value using put."""
    some_bidict = bi_cls(ELEMENTS)

    def _runner():
        with pytest.raises(ValueDuplicationError):
            some_bidict.put('key_with_dup_val', 'hydrogen')

    benchmark(_runner)


@pytest.mark.parametrize('bi_cls', BIDICT_TYPES)
def test_update_nodup(bi_cls, benchmark):
    """Test inserting new items with no duplication using update."""
    some_bidict = bi_cls(ELEMENTS)
    benchmark(some_bidict.update, UPDATE_NODUP)


@pytest.mark.parametrize('bi_cls', BIDICT_TYPES)
def test_update_withdup(bi_cls, benchmark):
    """Test inserting new items with value duplication using update."""
    some_bidict = bi_cls(ELEMENTS)

    def _runner():
        with pytest.raises(ValueDuplicationError):
            some_bidict.update(UPDATE_WITHDUPVAL)

    benchmark(_runner)


@pytest.mark.parametrize('bi_cls', BIDICT_TYPES)
def test_forceupdate_withdup(bi_cls, benchmark):
    """Test inserting new items with value duplication using forceupdate."""
    some_bidict = bi_cls(ELEMENTS)
    benchmark(some_bidict.forceupdate, UPDATE_WITHDUPVAL)
    assert some_bidict.inv['hydrogen'] == 'key_with_dup_val'

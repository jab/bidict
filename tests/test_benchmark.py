# -*- coding: utf-8 -*-
# Copyright 2017 Joshua Bronson. All Rights Reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Benchmarks."""

from bidict import OrderedBidict, ValueDuplicationError, bidict
import pytest

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


# pylint: disable=C0103,C0111

@pytest.mark.parametrize('B', BIDICT_TYPES)
def test_put_nodup(B, benchmark):  # noqa: N803
    """Test inserting a new item with no key or value duplication using put."""
    b = B(ELEMENTS)
    benchmark(b.put, 'K', 'potassium')


@pytest.mark.parametrize('B', BIDICT_TYPES)
def test_put_withdup(B, benchmark):  # noqa: N803
    """Test inserting a new item with a duplicate value using put."""
    b = B(ELEMENTS)

    def runner():
        with pytest.raises(ValueDuplicationError):
            b.put('key_with_dup_val', 'hydrogen')

    benchmark(runner)


@pytest.mark.parametrize('B', BIDICT_TYPES)
def test_update_nodup(B, benchmark):  # noqa: N803
    """Test inserting new items with no duplication using update."""
    b = B(ELEMENTS)
    benchmark(b.update, UPDATE_NODUP)


@pytest.mark.parametrize('B', BIDICT_TYPES)
def test_update_withdup(B, benchmark):  # noqa: N803
    """Test inserting new items with value duplication using update."""
    b = B(ELEMENTS)

    def runner():
        with pytest.raises(ValueDuplicationError):
            b.update(UPDATE_WITHDUPVAL)

    benchmark(runner)


@pytest.mark.parametrize('B', BIDICT_TYPES)
def test_forceupdate_withdup(B, benchmark):  # noqa: N803
    """Test inserting new items with value duplication using forceupdate."""
    b = B(ELEMENTS)
    benchmark(b.forceupdate, UPDATE_WITHDUPVAL)
    assert b.inv['hydrogen'] == 'key_with_dup_val'

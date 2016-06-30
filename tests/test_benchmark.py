from bidict import bidict, orderedbidict, ValueDuplicationError
import pytest

bidict_types = (bidict, orderedbidict)

elements = orderedbidict((
    ('H', 'hydrogen'), ('He', 'helium'),
    ('Li', 'lithium'), ('Be', 'beryllium'), ('B', 'boron'), ('C', 'carbon'),
    ('N', 'nitrogen'), ('O', 'oxygen'), ('F', 'fluorine'), ('Ne', 'neon'),
    ('Na', 'sodium'), ('Mg', 'magnesium'), ('Al', 'aluminum'), ('Si', 'silicon'),
    ('P', 'phosphorus'), ('S', 'sulfur'), ('Cl', 'chlorine'), ('Ar', 'argon'),
))

update_nodup = orderedbidict((
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

update_withdupval = orderedbidict(update_nodup, key_with_dup_val='hydrogen')


@pytest.mark.parametrize('B', bidict_types)
def test_put_nodup(B, benchmark):
    b = B(elements)
    benchmark(b.put, 'K', 'potassium')


@pytest.mark.parametrize('B', bidict_types)
def test_put_withdup(B, benchmark):
    b = B(elements)

    def runner():
        with pytest.raises(ValueDuplicationError):
            b.put('key_with_dup_val', 'hydrogen')

    benchmark(runner)


@pytest.mark.parametrize('B', bidict_types)
def test_update_nodup(B, benchmark):
    b = B(elements)
    benchmark(b.update, update_nodup)


@pytest.mark.parametrize('B', bidict_types)
def test_update_withdup(B, benchmark):
    b = B(elements)

    def runner():
        with pytest.raises(ValueDuplicationError):
            b.update(update_withdupval)

    benchmark(runner)


@pytest.mark.parametrize('B', bidict_types)
def test_forceupdate_withdup(B, benchmark):
    b = B(elements)
    benchmark(b.forceupdate, update_withdupval)
    assert b.inv['hydrogen'] == 'key_with_dup_val'

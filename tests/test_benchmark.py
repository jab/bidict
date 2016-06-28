from bidict import bidict, orderedbidict, ValueDuplicationError, OVERWRITE
import pytest


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

update_withdupval = bidict(update_nodup, key_with_dup_val='hydrogen')


def test_put_nodup(benchmark):
    elements_ = bidict(elements)
    benchmark(elements_.put, 'K', 'potassium')


def test_put_withdup(benchmark):
    elements_ = bidict(elements)

    def runner():
        with pytest.raises(ValueDuplicationError):
            elements_.put('key_with_dup_val', 'hydrogen')

    benchmark(runner)


def test_update_nodup(benchmark):
    elements_ = bidict(elements)
    benchmark(elements_.update, update_nodup)


def test_update_withdup(benchmark):
    elements_ = bidict(elements)

    def runner():
        with pytest.raises(ValueDuplicationError):
            elements_.update(update_withdupval)

    benchmark(runner)


def test_overwriting_putall_withdup(benchmark):
    elements_ = bidict(elements)
    benchmark(elements_.putall, update_withdupval,
              on_dup_key=OVERWRITE, on_dup_val=OVERWRITE, on_dup_kv=OVERWRITE)
    assert elements_.inv['hydrogen'] == 'key_with_dup_val'

from io import open
from setuptools import setup
from warnings import warn

try:
    with open('bidict/VERSION', encoding='utf8') as f:
        version = f.read().strip()
except Exception as e:
    version = '0.0.0'
    warn('Could not open bidict/VERSION, using bogus version (%s): %r' %
         (version, e))
try:
    with open('README.rst', encoding='utf8') as f:
        long_description = f.read()
except Exception as e:
    long_description = 'See https://bidict.readthedocs.org'
    warn('Could not open README.rst, using provisional long_description '
         '(%r): %r' % (long_description, e))

tests_require = [
    'coverage==4.3.4',
    'flake8==3.2.1',
    'hypothesis==3.6.1',
    'hypothesis-pytest==0.19.0',
    'py==1.4.31',
    'pydocstyle==1.1.1',
    'pytest==3.0.5',
    'pytest-benchmark==3.1.0a1',
    'pytest-cov==2.4.0',
    'Sphinx==1.5.1',
    'sortedcollections==0.4.2',
    'sortedcontainers==1.5.5',
]

setup(
    name='bidict',
    version=version,
    author='Joshua Bronson',
    author_email='jab@math.brown.edu',
    description='Efficient, Pythonic bidirectional map implementation and related functionality',
    long_description=long_description,
    keywords='dict, dictionary, mapping, bidirectional, bijection, bijective, injective, two-way, 2-way, double, inverse, reverse',
    url='https://github.com/jab/bidict',
    license='ISC',
    packages=['bidict'],
    package_data=dict(bidict=['VERSION']),
    zip_safe=True,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: ISC License (ISCL)',  # https://github.com/jab/bidict/pull/38#issuecomment-273007773
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Scientific/Engineering :: Mathematics',
        'Topic :: Software Development :: Libraries :: Python Modules',
        ],
    tests_require=tests_require,
    extras_require=dict(
        test=tests_require,
        dev=tests_require + ['pre-commit==0.10.1', 'tox==2.3.2'],
    ),
)

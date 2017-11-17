from io import open
from setuptools import setup
from warnings import warn


def from_file(filename, fallback):
    try:
        with open(filename, encoding='utf8') as f:
            return f.read().strip()
    except Exception as e:
        warn('Error opening file %r, using fallback %r: %s' % (filename, fallback, e))
        return fallback


version = from_file('bidict/VERSION', '0.0.0')
long_description = from_file('README.rst', 'See https://bidict.readthedocs.org').replace(
    ':doc:', '')  # :doc: breaks long_description rendering on PyPI


tests_require = [
    'hypothesis==3.34.1',
    'hypothesis-pytest==0.19.0',
    'py==1.5.2',
    'pytest==3.2.5',
    'pytest-benchmark==3.1.1',
    'sortedcollections==0.5.3',
    'sortedcontainers==1.5.7',
]

coverage_requires = [
    'coverage==4.4.2',
    'pytest-cov==2.5.1',
]

dev_requires = tests_require + coverage_requires + [
    'Sphinx==1.6.5',
    'flake8==3.5.0',
    'pre-commit==1.4.1',
    'pydocstyle==2.1.1',
    'pylint==1.7.4',
    'tox==2.9.1',
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
    license='Mozilla PL',
    packages=['bidict'],
    package_data=dict(bidict=['VERSION']),
    zip_safe=True,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Scientific/Engineering :: Mathematics',
        'Topic :: Software Development :: Libraries :: Python Modules',
        ],
    tests_require=tests_require,
    extras_require=dict(
        test=tests_require,
        coverage=coverage_requires,
        dev=dev_requires,
    ),
)

from io import open
from setuptools import setup, Command

try:
    with open('VERSION', encoding='utf8') as f:
        version = f.read()
except:
    version = '999999'
try:
    with open('README.rst', encoding='utf8') as f:
        long_description = f.read()
except:
    long_description = 'See https://bidict.readthedocs.org'

tests_require = [
    'tox',
    'pytest',
    'pytest-cov',
    'hypothesis',
    'hypothesis-pytest',
]

class PyTest(Command):
    user_options = []
    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        import subprocess
        import sys
        errno = subprocess.call(['py.test'])
        raise SystemExit(errno)

setup(
    name='bidict',
    version=version,
    author='Joshua Bronson',
    author_email='jab@math.brown.edu',
    description="Bidirectional dict with convenient slice syntax: d[65] = 'A' <-> d[:'A'] = 65",
    long_description=long_description,
    keywords='dict, dictionary, mapping, bidirectional, bijection, bijective, injective, two-way, 2-way, double, inverse, reverse',
    url='https://github.com/jab/bidict',
    license='ISCL',
    py_modules=['bidict'],
    data_files=[('', ['VERSION'])],
    zip_safe=True,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: ISC License (ISCL)',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Scientific/Engineering :: Mathematics',
        'Topic :: Software Development :: Libraries :: Python Modules',
        ],
    cmdclass=dict(test=PyTest),
    tests_require=tests_require,
    extras_require=dict(
        dev=['pre-commit'] + tests_require,
        test=tests_require,
    ),
)

from io import open
from setuptools import setup, Command
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
        from subprocess import call
        errno = call(['py.test'])
        raise SystemExit(errno)

setup(
    name='bidict',
    version=version,
    author='Joshua Bronson',
    author_email='jab@math.brown.edu',
    description='Efficient, Pythonic bidirectional map implementation and related functionality',
    long_description=long_description,
    keywords='dict, dictionary, mapping, bidirectional, bijection, bijective, injective, two-way, 2-way, double, inverse, reverse',
    url='https://github.com/jab/bidict',
    license='ISCL',
    packages=['bidict'],
    package_data=dict(bidict=['VERSION']),
    zip_safe=True,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: ISC License (ISCL)',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
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

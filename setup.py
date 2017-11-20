# -*- coding: utf-8 -*-
# Copyright 2017 Joshua Bronson. All Rights Reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
setup.py
"""

from io import open  # pylint: disable=redefined-builtin

from setuptools import setup

# Fetch bidict's package metadata from bidict/metadata.py.
# Must use exec(open(...)) because we haven't been installed yet.
METADATA = {'__BIDICT_SETUPPY__FILE__': __file__}
exec(open('bidict/metadata.py').read().encode('utf8'), METADATA)  # pylint: disable=exec-used

TESTS_REQ = [
    'hypothesis==3.38.0',
    'hypothesis-pytest==0.19.0',
    'py==1.5.2',
    'pytest==3.2.5',
    'pytest-benchmark==3.1.1',
    'sortedcollections==0.5.3',
    'sortedcontainers==1.5.7',
]
COVERAGE_REQ = [
    'coverage==4.4.2',
    'pytest-cov==2.5.1',
]
DEV_REQ = TESTS_REQ + COVERAGE_REQ + [
    'Sphinx==1.6.5',
    'flake8==3.5.0',
    'pre-commit==1.4.1',
    'pydocstyle==2.1.1',
    'pylint==1.7.4',
    'tox==2.9.1',
]

setup(
    name='bidict',
    version=METADATA['__version__'],
    author=METADATA['__author__'],
    author_email=METADATA['__email__'],
    description='Efficient, Pythonic bidirectional map implementation and related functionality',
    long_description=METADATA['__long_description__'],
    keywords='dict, dictionary, mapping, datastructure, '
             'bimap, bijection, bijective, injective, inverse, reverse, '
             'bidirectional, two-way, 2-way',
    url='https://github.com/jab/bidict',
    license=METADATA['__license__'],
    packages=['bidict'],
    package_data=dict(bidict=['VERSION']),
    zip_safe=False,  # Don't zip. (We're zip-safe but prefer not to.)
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    tests_require=TESTS_REQ,
    extras_require=dict(
        test=TESTS_REQ,
        coverage=COVERAGE_REQ,
        dev=DEV_REQ,
    ),
)

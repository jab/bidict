# -*- coding: utf-8 -*-
# Copyright 2017 Joshua Bronson. All Rights Reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""setup.py"""

from io import open  # pylint: disable=redefined-builtin

from setuptools import setup

# Fetch bidict's package metadata from bidict/metadata.py.
# Must use exec(open(...)) because we haven't been installed yet.
METADATA = {}
exec(open('bidict/metadata.py').read().encode('utf8'), METADATA)  # pylint: disable=exec-used

try:
    LONG_DESCRIPTION = open('README.rst').read().replace(
        ':doc:', '(doc:)'  # :doc: breaks rendering on PyPI
    )
except:  # noqa; pylint: disable=bare-except
    LONG_DESCRIPTION = 'See https://bidict.readthedocs.io'

SETUP_REQ = [
    'pytest-runner',
    'setuptools_scm',
]

TESTS_REQ = [
    'hypothesis>=3.38.4,<4',
    'hypothesis-pytest>=0.19.0,<1',
    'py>=1.5.2,<2',
    'pytest>=3.2.5,<4',
    'pytest-benchmark>=3.1.1,<4',
    'sortedcollections>=0.5.3,<1',
    'sortedcontainers>=1.5.7,<2',
]

COVERAGE_REQ = [
    'coverage>=4.4.2,<5',
    'pytest-cov>=2.5.1,<3',
]

DEV_REQ = SETUP_REQ + TESTS_REQ + COVERAGE_REQ + [
    'Sphinx>=1.6.5,<2',
    'flake8>=3.5.0,<4',
    'pre-commit>=1.4.1,<2',
    'pydocstyle>=2.1.1,<3',
    'pylint>=1.7.4,<2',
    'tox>=2.9.1,<3',
]

setup(
    name='bidict',
    use_scm_version=True,
    author=METADATA['__author__'],
    author_email=METADATA['__email__'],
    description=METADATA['__description__'],
    long_description=LONG_DESCRIPTION,
    keywords='dict, dictionary, mapping, datastructure, '
             'bimap, bijection, bijective, injective, inverse, reverse, '
             'bidirectional, two-way, 2-way',
    url='https://github.com/jab/bidict',
    license=METADATA['__license__'],
    packages=['bidict'],
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
    setup_requires=SETUP_REQ,
    tests_require=TESTS_REQ,
    extras_require=dict(
        test=TESTS_REQ,
        coverage=COVERAGE_REQ,
        dev=DEV_REQ,
    ),
)

# -*- coding: utf-8 -*-
# Copyright 2018 Joshua Bronson. All Rights Reserved.
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
        ':doc:', ''  # :doc: breaks rendering on PyPI
    ).replace(  # the _static content isn't available on PyPI
        './_static/logo.png', 'https://github.com/jab/bidict/raw/master/_static/logo.png'
    )
except:  # noqa; pylint: disable=bare-except
    LONG_DESCRIPTION = 'See https://bidict.readthedocs.io'

SETUP_REQS = [
    'pytest-runner',
    'setuptools_scm',
]

TEST_REQS = [
    'hypothesis<4',
    'hypothesis-pytest<1',
    'py<2',
    'pytest<4',
    'pytest-benchmark<4',
    'sortedcollections<1',
    'sortedcontainers<2',
]

COVERAGE_REQS = [
    'coverage<5',
    'pytest-cov<3',
]

DEV_REQ = SETUP_REQS + TEST_REQS + COVERAGE_REQS + [
    'Sphinx<2',
    'pre-commit<2',
    'tox<3',
    # Peg to more specific versions of the following dependencies since they'd
    # have a higher chance of breaking CI otherwise. Upgrade to newer versions
    # manually to have a chance to fix any resulting breakage.
    'flake8<3.6',
    'pydocstyle<2.2',
    'pylint<1.9',
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
    setup_requires=SETUP_REQS,
    tests_require=TEST_REQS,
    extras_require=dict(
        test=TEST_REQS,
        coverage=COVERAGE_REQS,
        dev=DEV_REQ,
    ),
)

# -*- coding: utf-8 -*-
# Copyright 2018 Joshua Bronson. All Rights Reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""A setuptools-based setup module.

Ref: https://github.com/pypa/sampleproject/blob/master/setup.py
"""

from codecs import open as c_open
from os.path import abspath, dirname, join

from setuptools import setup


CWD = abspath(dirname(__file__))

# Get bidict's package metadata from ./bidict/metadata.py.
METADATA_PATH = join(CWD, 'bidict', 'metadata.py')
try:
    from importlib.util import module_from_spec, spec_from_file_location
except ImportError:  # Python < 3.5
    try:
        from importlib.machinery import SourceFileLoader
    except ImportError:  # Python < 3.3 - treat as Python 2 (otherwise unsupported).
        from imp import load_source
        METADATA = load_source('metadata', METADATA_PATH)
    else:  # Python 3.3 or 3.4
        LOADER = SourceFileLoader('metadata', METADATA_PATH)
        METADATA = LOADER.load_module('metadata')  # pylint: disable=deprecated-method
else:
    SPEC = spec_from_file_location('metadata', METADATA_PATH)
    METADATA = module_from_spec(SPEC)
    SPEC.loader.exec_module(METADATA)


with c_open(join(CWD, 'README.rst'), encoding='utf-8') as f:
    LONG_DESCRIPTION = f.read()

SETUP_REQS = [
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

# Split out coverage from test requirements since it slows down the tests.
COVERAGE_REQS = [
    'coverage<5',
    'pytest-cov<3',
]

DOCS_REQS = [
    'Sphinx<2',
]

DEV_REQ = SETUP_REQS + TEST_REQS + COVERAGE_REQS + DOCS_REQS + [
    'pre-commit<2',
    'tox<4',
    # The following dependencies have a higher chance of suddenly causing CI to fail after updating
    # even between minor versions so pin to currently-working minor versions. Upgrade to newer
    # minor versions manually to have a chance to fix any resulting breakage before it hits CI.
    # *** Keep these in sync with the versions in .travis.yml and .pre-commit-config.yaml ***
    'flake8<3.6',
    'pydocstyle<2.2',
    'pylint<2.2',
]

setup(
    name='bidict',
    use_scm_version={
        'version_scheme': 'guess-next-dev',
        'local_scheme': 'dirty-tag',
        'write_to': 'bidict/_version.py',
    },
    author=METADATA.__author__,
    author_email=METADATA.__email__,
    description=METADATA.__description__,
    long_description=LONG_DESCRIPTION,
    keywords=METADATA.__keywords__,
    url=METADATA.__url__,
    license=METADATA.__license__,
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
    setup_requires=SETUP_REQS,  # required so pip < 10 install works (no PEP-517/518 support)
    # for more details see https://www.python.org/dev/peps/pep-0518/#rationale
    tests_require=TEST_REQS,
    extras_require=dict(
        test=TEST_REQS,
        coverage=COVERAGE_REQS,
        docs=DOCS_REQS,
        dev=DEV_REQ,
    ),
)

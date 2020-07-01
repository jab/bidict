# -*- coding: utf-8 -*-
# Copyright 2009-2020 Joshua Bronson. All Rights Reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""A setuptools-based setup module.

Ref: https://github.com/pypa/sampleproject/blob/master/setup.py
"""

import sys
from codecs import open as c_open
from os.path import abspath, dirname, join
from warnings import warn

from setuptools import setup


PY2_ERR = """
This version of bidict does not support Python 2.
Either use bidict 0.18.3,
the last release with Python 2 support,
or use Python 3.

Also ensure you are using pip >= 9.0.1 to install bidict.

See python3statement.org for more info.
"""

if sys.version_info < (3,):
    sys.exit(PY2_ERR)
elif sys.version_info < (3, 5):
    warn('This version of bidict is untested on Python < 3.5 and may not work.')


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

# Manually keep these version pins in sync with those in .travis.yml and .pre-commit-config.yaml.

SPHINX_REQS = [
    'Sphinx < 3',
    # Sphinx's docutils pin has no upper bound. Pin to 0.15.2 pending sphinx-doc/sphinx#6594.
    # (Pulling 0.15 previously broke "make doctest" with SyntaxError under Python 2.7.)
    'docutils == 0.15.2',
]

DOCS_REQS = SPHINX_REQS

TEST_REQS = [
    'hypothesis < 5',
    'py < 2',
    'pytest < 6',
    'pytest-benchmark >= 3.2.0, < 4',
    'sortedcollections < 2',
    'sortedcontainers < 3',
    # pytest's doctest support doesn't support Sphinx extensions
    # (https://www.sphinx-doc.org/en/latest/usage/extensions/doctest.html)
    # so †est the code in the Sphinx docs using Sphinx's own doctest support.
    DOCS_REQS,
]

# Split out coverage from test requirements since it slows down the tests.
COVERAGE_REQS = [
    'coverage < 5',
    'pytest-cov < 3',
]

# The following dependencies have a higher chance of suddenly causing CI to fail after updating
# even between minor versions, so pin to currently-working minor versions. Upgrade to newer
# minor versions manually to have a chance to fix any resulting breakage before it hits CI.
FLAKE8_REQ = 'flake8 < 3.8'
PYDOCSTYLE_REQ = 'pydocstyle < 3.1'
PYLINT_REQS = [
    # Pin to exact versions of Pylint and Astroid, which don't follow semver.
    # See https://github.com/PyCQA/astroid/issues/651#issuecomment-469021040
    'pylint == 2.4.3',
    'astroid == 2.3.2',
]

LINT_REQS = [
    FLAKE8_REQ,
    PYDOCSTYLE_REQ,
] + PYLINT_REQS

DEV_REQS = SETUP_REQS + DOCS_REQS + TEST_REQS + COVERAGE_REQS + LINT_REQS + [
    'pre-commit < 2',
    'tox < 4',
]

EXTRAS_REQS = dict(
    docs=DOCS_REQS,
    test=TEST_REQS,
    coverage=COVERAGE_REQS,
    lint=LINT_REQS,
    dev=DEV_REQS,
    sphinx=SPHINX_REQS,
    flake8=[FLAKE8_REQ],
    pydocstyle=[PYDOCSTYLE_REQ],
    pylint=PYLINT_REQS,
)

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
    python_requires='>=3',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    setup_requires=SETUP_REQS,  # required so pip < 10 install works (no PEP-517/518 support)
    # for more details see https://www.python.org/dev/peps/pep-0518/#rationale
    tests_require=TEST_REQS,
    extras_require=EXTRAS_REQS,
)

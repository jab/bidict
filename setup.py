# -*- coding: utf-8 -*-
# Copyright 2009-2021 Joshua Bronson. All Rights Reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""A setuptools-based setup module.

Ref: https://github.com/pypa/sampleproject/blob/main/setup.py
"""

import sys
from os.path import abspath, dirname, join
from warnings import warn

from setuptools import setup


PY2_ERR = """
This version of bidict does not support Python 2.
Either use bidict 0.18.4,
the last release with Python 2 support,
or use Python 3.

Also ensure you are using pip >= 9.0.1 to install bidict.

See python3statement.org for more info.
"""

if sys.version_info < (3,):
    sys.exit(PY2_ERR)
elif sys.version_info < (3, 6):
    warn('This version of bidict is untested on Python < 3.6 and may not work.')

from importlib.util import module_from_spec, spec_from_file_location

CWD = abspath(dirname(__file__))

# Get bidict's package metadata from ./bidict/metadata.py.
METADATA_PATH = join(CWD, 'bidict', 'metadata.py')
SPEC = spec_from_file_location('metadata', METADATA_PATH)
if not SPEC:
    raise FileNotFoundError('bidict/metadata.py')
METADATA = module_from_spec(SPEC)
SPEC.loader.exec_module(METADATA)  # type: ignore

with open(join(CWD, 'README.rst'), encoding='utf-8') as f:
    LONG_DESCRIPTION = f.read()

setup(
    name='bidict',
    author=METADATA.__author__,  # type: ignore
    author_email=METADATA.__email__,  # type: ignore
    description=METADATA.__description__,  # type: ignore
    long_description=LONG_DESCRIPTION,
    long_description_content_type='text/x-rst',
    keywords=METADATA.__keywords__,  # type: ignore
    url=METADATA.__url__,  # type: ignore
    license=METADATA.__license__,  # type: ignore
    packages=['bidict'],
    include_package_data=True,
    zip_safe=False,  # Don't zip. (We're zip-safe but prefer not to.)
    python_requires='>=3.6',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Typing :: Typed',
    ],
)

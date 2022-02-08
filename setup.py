# -*- coding: utf-8 -*-
# Copyright 2009-2022 Joshua Bronson. All Rights Reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""A setuptools-based setup module.

Ref: https://github.com/pypa/sampleproject/blob/main/setup.py
"""

import sys
import types
from os.path import abspath, dirname, join

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
elif sys.version_info < (3, 7):
    sys.exit('Python < 3.7 is not supported by this version of bidict.')


CWD = abspath(dirname(__file__))

with open(join(CWD, 'README.rst'), encoding='utf8') as f:
    LONG_DESCRIPTION = f.read()

# Get bidict's package metadata from ./bidict/metadata.py.
metadata = {}
with open(join(CWD, 'bidict', 'metadata.py'), encoding='utf8') as f:
    exec(f.read(), metadata)
metadata = types.SimpleNamespace(**metadata)


setup(
    name='bidict',
    author=metadata.__author__,
    author_email=metadata.__email__,
    description=metadata.__description__,
    long_description=LONG_DESCRIPTION,
    long_description_content_type='text/x-rst',
    keywords=metadata.__keywords__,
    url=metadata.__url__,
    license=metadata.__license__,
    packages=['bidict'],
    include_package_data=True,
    zip_safe=False,  # Don't zip. (We're zip-safe but prefer not to.)
    python_requires='>=3.7',
    project_urls=metadata.__project_urls__,
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Typing :: Typed',
    ],
)

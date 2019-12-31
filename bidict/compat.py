# -*- coding: utf-8 -*-
# Copyright 2009-2020 Joshua Bronson. All Rights Reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


"""Compatibility helpers."""

from platform import python_implementation
from sys import version_info


# The "#:" below tell Sphinx to include these members in the API docs.
PYMAJOR, PYMINOR = version_info[:2]  #:
PY2 = PYMAJOR == 2  #:
PYIMPL = python_implementation()  #:
CPY = PYIMPL == 'CPython'  #:
PYPY = PYIMPL == 'PyPy'  #:
DICTS_ORDERED = PYPY or (CPY and (PYMAJOR, PYMINOR) >= (3, 6))  #:

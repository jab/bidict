# -*- coding: utf-8 -*-
# Copyright 2017 Joshua Bronson. All Rights Reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
Test :attr:`bidict.__version__`.
"""

import bidict


def test_version():
    """Ensure the module has a ``__version__`` attribute."""
    assert bidict.__version__

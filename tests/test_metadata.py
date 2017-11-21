# -*- coding: utf-8 -*-
# Copyright 2017 Joshua Bronson. All Rights Reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Test bidict metadata."""

import bidict


# pylint: disable=all
# (otherwise pylint flags duplicate code in bidict/metadata.py)
META_ATTRS = [
    '__author__',
    '__maintainer__',
    '__copyright__',
    '__email__',
    '__credits__',
    '__description__',
    '__license__',
    '__status__',
    '__version__',
]


def test_metadata():
    """Ensure bidict has expected metadata attributes."""
    for i in META_ATTRS:
        assert getattr(bidict, i)

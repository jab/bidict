# -*- coding: utf-8 -*-
# Copyright 2017 Joshua Bronson. All Rights Reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Provides bidict duplication behaviors."""

from ._marker import _Marker


class DuplicationPolicy(_Marker):
    """
    Provide RAISE, OVERWRITE, and IGNORE duplication policies.

    .. py:attribute:: RAISE

        Raise an exception when a duplication is encountered.

    .. py:attribute:: OVERWRITE

        Overwrite an existing item when a duplication is encountered.

    .. py:attribute:: IGNORE

        Keep the existing item and ignore the new item when a duplication is
        encountered.
    """


DuplicationPolicy.RAISE = RAISE = DuplicationPolicy('RAISE')
DuplicationPolicy.OVERWRITE = OVERWRITE = DuplicationPolicy('OVERWRITE')
DuplicationPolicy.IGNORE = IGNORE = DuplicationPolicy('IGNORE')

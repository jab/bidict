# -*- coding: utf-8 -*-
# Copyright 2018 Joshua Bronson. All Rights Reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


"""Provides bidict duplication behaviors."""


from ._marker import _Marker


class DuplicationPolicy(object):
    """Provides bidict's duplication policies.

    See also :ref:`values-must-be-unique`
    """

    __slots__ = ()

    #: Raise an exception when a duplication is encountered.
    RAISE = _Marker('RAISE')

    #: Overwrite an existing item when a duplication is encountered.
    OVERWRITE = _Marker('OVERWRITE')

    #: Keep the existing item and ignore the new item when a duplication is encountered.
    IGNORE = _Marker('IGNORE')


RAISE = DuplicationPolicy.RAISE
OVERWRITE = DuplicationPolicy.OVERWRITE
IGNORE = DuplicationPolicy.IGNORE

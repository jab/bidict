# -*- coding: utf-8 -*-
# Copyright 2009-2020 Joshua Bronson. All Rights Reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


"""Provides sentinels used internally in bidict."""

from enum import Enum


class _Sentinel(Enum):
    #: The result of looking up a missing key (or inverse key).
    MISS = 'MISS'
    #: No-op.
    NOOP = 'NOOP'

    def __repr__(self):
        return '<%s>' % self.name  # pragma: no cover


_MISS = _Sentinel.MISS
_NOOP = _Sentinel.NOOP

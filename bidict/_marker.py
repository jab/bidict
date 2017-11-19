# -*- coding: utf-8 -*-
# Copyright 2017 Joshua Bronson. All Rights Reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Provides :class:`_Marker` for representing singletons."""


class _Marker(object):
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return '<%s>' % self.name  # pragma: no cover

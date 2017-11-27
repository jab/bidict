# -*- coding: utf-8 -*-
# Copyright 2017 Joshua Bronson. All Rights Reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Implements :class:`classproperty`."""


class classproperty(property):  # noqa: N801; pylint: disable=invalid-name
    """TODO"""

    def __get__(self, cls, owner):
        return self.fget.__get__(None, owner)()  # pylint: disable=no-member

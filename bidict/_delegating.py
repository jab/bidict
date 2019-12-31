# -*- coding: utf-8 -*-
# Copyright 2009-2020 Joshua Bronson. All Rights Reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


"""Provides :class:`_DelegatingMixin`."""


class _DelegatingMixin:
    """Provide optimized implementations of several methods by delegating to backing dicts.

    Used to override less efficient implementations inherited by :class:`~collections.abc.Mapping`.
    """

    __slots__ = ()

    def __iter__(self):
        """Iterator over the contained items."""
        return iter(self._fwdm)  # pylint: disable=protected-access

    def keys(self):
        """A set-like object providing a view on the contained keys."""
        return self._fwdm.keys()  # pylint: disable=protected-access

    def values(self):
        """A set-like object providing a view on the contained values."""
        return self._invm.keys()  # pylint: disable=protected-access

    def items(self):
        """A set-like object providing a view on the contained items."""
        return self._fwdm.items()  # pylint: disable=protected-access

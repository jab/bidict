# -*- coding: utf-8 -*-
# Copyright 2009-2020 Joshua Bronson. All Rights Reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Provides :class:`defaultbidict`, bidirectional defaultdict"""

from collections.abc import Hashable
from ._mut import MutableBidict
from ._delegating import _DelegatingMixin


class defaultbidict(_DelegatingMixin, MutableBidict):  # noqa: N801; pylint: disable=invalid-name
    """Bidirectional defaultdict"""
    __slots__ = ('_default_factory', )

    def __init__(self, *args, **kw):
        """Bidirectional defaultdict.
        Provide :attr:`default` to set default factory"""
        default_factory = kw.pop('default', None)
        super().__init__(*args, **kw)
        if default_factory is not None and not (default_factory, Hashable):
            raise TypeError('Default value must be hashable')
        self._default_factory = default_factory

    def copy(self):
        """A shallow copy."""
        cp = super().copy()  # pylint: disable=invalid-name
        cp._default_factory = self._default_factory  # pylint: disable=protected-access
        return cp

    def __missing__(self, key):
        if self._default_factory is None:
            raise KeyError(key)
        self[key] = value = self._default_factory()
        return value

    def __getitem__(self, key):
        try:
            return super().__getitem__(key)
        except KeyError:
            return self.__missing__(key)

# -*- coding: utf-8 -*-
# Copyright 2009-2020 Joshua Bronson. All Rights Reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


"""Provide :class:`_DelegatingBidict`."""

from typing import Iterator, KeysView, ItemsView

from ._base import BidictBase, KT, VT


class _DelegatingBidict(BidictBase[KT, VT]):
    """Provide optimized implementations of several methods by delegating to backing dicts.

    Used to override less efficient implementations inherited by :class:`~collections.abc.Mapping`.
    """

    __slots__ = ()

    def __iter__(self) -> Iterator[KT]:
        """Iterator over the contained keys."""
        return iter(self._fwdm)  # pylint: disable=protected-access

    def keys(self) -> KeysView[KT]:
        """A set-like object providing a view on the contained keys."""
        return self._fwdm.keys()  # pylint: disable=protected-access

    def values(self) -> KeysView[VT]:
        """A set-like object providing a view on the contained values."""
        return self._invm.keys()  # pylint: disable=protected-access

    def items(self) -> ItemsView[KT, VT]:
        """A set-like object providing a view on the contained items."""
        return self._fwdm.items()  # pylint: disable=protected-access

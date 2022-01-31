# Copyright 2009-2022 Joshua Bronson. All Rights Reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


"""Provide typing-related objects."""

import typing as _t
from enum import Enum


KT = _t.TypeVar('KT')
VT = _t.TypeVar('VT')
IterItems = _t.Iterable[_t.Tuple[KT, VT]]
MapOrIterItems = _t.Union[_t.Mapping[KT, VT], IterItems[KT, VT]]


class NONEType(Enum):
    """Sentinel used to represent none/missing when None itself can't be used."""

    NONE = 'NONE'

    def __repr__(self) -> str:
        return '<NONE>'


NONE = NONEType.NONE
OKT = _t.Union[KT, NONEType]  #: optional key type
OVT = _t.Union[VT, NONEType]  #: optional value type

DT = _t.TypeVar('DT')  #: for default arguments
ODT = _t.Union[DT, NONEType]


class ItemsView(_t.ItemsView[KT, VT], _t.Reversible[_t.Tuple[KT, VT]]):
    """All ItemsViews that bidicts provide are Reversible."""


class KeysView(_t.KeysView[KT], _t.Reversible[KT], _t.ValuesView[_t.Any]):
    """All KeysViews that bidicts provide are Reversible and are also ValuesViews.

    Since the keys of a bidict are the values of its inverse (and vice versa),
    calling .values() on a bidict returns the same result as calling .keys() on its inverse,
    specifically a KeysView[KT] object that is also a ValuesView[VT].
    """

# Copyright 2009-2022 Joshua Bronson. All Rights Reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


"""Provide typing-related objects."""

import collections.abc
import typing as _t


KT = _t.TypeVar('KT')
VT = _t.TypeVar('VT')
IterItems = _t.Iterable[_t.Tuple[KT, VT]]
MapOrIterItems = _t.Union[_t.Mapping[KT, VT], IterItems[KT, VT]]

DT = _t.TypeVar('DT')  #: for default arguments
VDT = _t.Union[VT, DT]


class _BareReprMeta(type):
    def __repr__(cls) -> str:
        return f'<{cls.__name__}>'


class _NONE(metaclass=_BareReprMeta):
    """Sentinel type used to represent 'missing'."""


OKT = _t.Union[KT, _NONE]  #: optional key type
OVT = _t.Union[VT, _NONE]  #: optional value type


class ItemsView(_t.ItemsView[KT, VT], _t.Reversible[_t.Tuple[KT, VT]]):
    """All ItemsViews that bidicts provide are reversible."""


class KeysView(_t.KeysView[KT], _t.Reversible[KT], collections.abc.ValuesView):
    """All KeysViews that bidicts provide are reversible.

    In addition, since the keys of a bidict are the values of its inverse (and vice versa),
    calling .values() on a bidict returns the same result as calling .keys() on its inverse,
    specifically a KeysView[KT] object that is also a ValuesView[VT].
    """

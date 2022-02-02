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


class MissingT(Enum):
    """Sentinel used to represent none/missing when None itself can't be used."""

    MISSING = 'MISSING'

    def __repr__(self) -> str:
        return '<MISSING>'


MISSING = MissingT.MISSING
OKT = _t.Union[KT, MissingT]  #: optional key type
OVT = _t.Union[VT, MissingT]  #: optional value type

DT = _t.TypeVar('DT')  #: for default arguments
ODT = _t.Union[DT, MissingT]

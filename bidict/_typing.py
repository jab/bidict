# Copyright 2009-2023 Joshua Bronson. All rights reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


"""Provide typing-related objects."""

from __future__ import annotations

import typing as t
from enum import Enum


KT = t.TypeVar('KT')
VT = t.TypeVar('VT')


Items: t.TypeAlias = 't.Iterable[tuple[KT, VT]]'
MapOrItems: t.TypeAlias = 't.Mapping[KT, VT] | Items[KT, VT]'
ItemsIter: t.TypeAlias = 't.Iterator[tuple[KT, VT]]'


class MissingT(Enum):
    """Sentinel used to represent none/missing when None itself can't be used."""

    MISSING = 'MISSING'

    def __repr__(self) -> str:
        return '<MISSING>'


MISSING: t.Final[t.Literal[MissingT.MISSING]] = MissingT.MISSING
OKT: t.TypeAlias = 'KT | MissingT'  #: optional key type
OVT: t.TypeAlias = 'VT | MissingT'  #: optional value type

DT = t.TypeVar('DT')  #: for default arguments
ODT: t.TypeAlias = 'DT | MissingT'  #: optional default arg type

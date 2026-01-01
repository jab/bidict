# Copyright 2009-2026 Joshua Bronson. All rights reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


"""Provide typing-related objects."""

from __future__ import annotations

import typing as t
from collections.abc import Iterable
from collections.abc import Iterator
from enum import Enum


KT = t.TypeVar('KT')
VT = t.TypeVar('VT')
VT_co = t.TypeVar('VT_co', covariant=True)
MissingT = Enum('MissingT', {'MISSING': 'MISSING'})
MISSING: t.Final[t.Literal[MissingT.MISSING]] = MissingT.MISSING
OKT = t.Union[KT, MissingT]  #: optional key type
OVT = t.Union[VT, MissingT]  #: optional value type
DT = t.TypeVar('DT')  #: for default arguments
ODT = t.Union[DT, MissingT]  #: optional default arg type

Items = Iterable[tuple[KT, VT]]
ItemsIter = Iterator[tuple[KT, VT]]


@t.runtime_checkable
class Maplike(t.Protocol[KT, VT_co]):
    """Like typeshed's SupportsKeysAndGetItem, but usable at runtime."""

    def keys(self) -> Iterable[KT]: ...
    def __getitem__(self, __key: KT) -> VT_co: ...


MapOrItems = t.Union[Maplike[KT, VT], Items[KT, VT]]

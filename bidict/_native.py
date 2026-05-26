# Copyright 2009-2026 Joshua Bronson. All rights reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Optional native helpers for accelerating selected bidict operations."""

from __future__ import annotations

import typing as t
from collections.abc import Iterable

from ._dup import OnDup


Items = Iterable[tuple[t.Any, t.Any]]
BuildBidictMaps: t.TypeAlias = t.Callable[[Items, OnDup], tuple[dict[t.Any, t.Any], dict[t.Any, t.Any]]]
build_bidict_maps: BuildBidictMaps | None


if t.TYPE_CHECKING:
    build_bidict_maps = None

    def _build_bidict_maps_impl(
        items: Items,
        on_dup_key: str,
        on_dup_val: str,
    ) -> tuple[dict[t.Any, t.Any], dict[t.Any, t.Any]]: ...

else:
    try:
        from bidict_base_opt_native import build_bidict_maps as _build_bidict_maps_impl
    except ModuleNotFoundError as exc:
        if exc.name != 'bidict_base_opt_native':
            raise
        build_bidict_maps: BuildBidictMaps | None = None
    else:

        def build_bidict_maps(items: Items, on_dup: OnDup) -> tuple[dict[t.Any, t.Any], dict[t.Any, t.Any]]:
            return _build_bidict_maps_impl(items, on_dup.key.name, on_dup.val.name)

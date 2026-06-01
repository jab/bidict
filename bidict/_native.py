# Copyright 2009-2026 Joshua Bronson. All rights reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Optional native helpers for accelerating selected bidict operations."""

from __future__ import annotations

import os
import sys
import typing as t
from collections.abc import Iterable
from collections.abc import Mapping

from ._dup import OnDup


_DISABLE_NATIVE_ENVVAR = 'BIDICT_DISABLE_NATIVE'
_DISABLE_NATIVE_TRUE_VALUES = frozenset({'1', 'true', 'yes'})
Items = Iterable[tuple[t.Any, t.Any]]
BuildBidictMaps: t.TypeAlias = t.Callable[[Items, OnDup], tuple[dict[t.Any, t.Any], dict[t.Any, t.Any]]]
UpdateBidictMaps: t.TypeAlias = t.Callable[
    [dict[t.Any, t.Any], dict[t.Any, t.Any], Items, OnDup],
    tuple[dict[t.Any, t.Any], dict[t.Any, t.Any]],
]
BuildBidictMapsFromMapping: t.TypeAlias = t.Callable[
    [Mapping[t.Any, t.Any], OnDup], tuple[dict[t.Any, t.Any], dict[t.Any, t.Any]]
]
UpdateBidictMapsFromMapping: t.TypeAlias = t.Callable[
    [dict[t.Any, t.Any], dict[t.Any, t.Any], Mapping[t.Any, t.Any], OnDup],
    tuple[dict[t.Any, t.Any], dict[t.Any, t.Any]],
]
build_bidict_maps: BuildBidictMaps | None
update_bidict_maps: UpdateBidictMaps | None
build_bidict_maps_from_mapping: BuildBidictMapsFromMapping | None
update_bidict_maps_from_mapping: UpdateBidictMapsFromMapping | None


def _native_disabled() -> bool:
    value = os.getenv(_DISABLE_NATIVE_ENVVAR)
    return value is not None and value.lower() in _DISABLE_NATIVE_TRUE_VALUES


def _native_supported_runtime() -> bool:
    return sys.implementation.name == 'cpython'


if t.TYPE_CHECKING:
    build_bidict_maps = None
    update_bidict_maps = None
    build_bidict_maps_from_mapping = None
    update_bidict_maps_from_mapping = None

    def _build_bidict_maps_impl(
        items: Items,
        on_dup_key: str,
        on_dup_val: str,
    ) -> tuple[dict[t.Any, t.Any], dict[t.Any, t.Any]]: ...

    def _update_bidict_maps_impl(
        fwd: dict[t.Any, t.Any],
        inv: dict[t.Any, t.Any],
        items: Items,
        on_dup_key: str,
        on_dup_val: str,
    ) -> tuple[dict[t.Any, t.Any], dict[t.Any, t.Any]]: ...

    def _build_bidict_maps_from_mapping_impl(
        mapping: Mapping[t.Any, t.Any],
        on_dup_key: str,
        on_dup_val: str,
    ) -> tuple[dict[t.Any, t.Any], dict[t.Any, t.Any]]: ...

    def _update_bidict_maps_from_mapping_impl(
        fwd: dict[t.Any, t.Any],
        inv: dict[t.Any, t.Any],
        mapping: Mapping[t.Any, t.Any],
        on_dup_key: str,
        on_dup_val: str,
    ) -> tuple[dict[t.Any, t.Any], dict[t.Any, t.Any]]: ...

else:
    if _native_disabled() or not _native_supported_runtime():
        build_bidict_maps: BuildBidictMaps | None = None
        update_bidict_maps: UpdateBidictMaps | None = None
        build_bidict_maps_from_mapping: BuildBidictMapsFromMapping | None = None
        update_bidict_maps_from_mapping: UpdateBidictMapsFromMapping | None = None
    else:
        try:
            from bidict_base_opt_native import bidict_base_opt_native as _native_ext
        except ModuleNotFoundError as exc:
            if exc.name != 'bidict_base_opt_native':
                raise
            build_bidict_maps = None
            update_bidict_maps = None
            build_bidict_maps_from_mapping = None
            update_bidict_maps_from_mapping = None
        else:
            _build_bidict_maps_impl = _native_ext.build_bidict_maps
            _update_bidict_maps_impl = getattr(_native_ext, 'update_bidict_maps', None)
            _build_bidict_maps_from_mapping_impl = getattr(_native_ext, 'build_bidict_maps_from_mapping', None)
            _update_bidict_maps_from_mapping_impl = getattr(_native_ext, 'update_bidict_maps_from_mapping', None)

            def build_bidict_maps(items: Items, on_dup: OnDup) -> tuple[dict[t.Any, t.Any], dict[t.Any, t.Any]]:
                return _build_bidict_maps_impl(items, on_dup.key.name, on_dup.val.name)

            if _build_bidict_maps_from_mapping_impl is None:
                build_bidict_maps_from_mapping = None
            else:

                def build_bidict_maps_from_mapping(
                    mapping: Mapping[t.Any, t.Any], on_dup: OnDup
                ) -> tuple[dict[t.Any, t.Any], dict[t.Any, t.Any]]:
                    return _build_bidict_maps_from_mapping_impl(mapping, on_dup.key.name, on_dup.val.name)

            if _update_bidict_maps_impl is None:
                update_bidict_maps = None
            else:

                def update_bidict_maps(
                    fwd: dict[t.Any, t.Any],
                    inv: dict[t.Any, t.Any],
                    items: Items,
                    on_dup: OnDup,
                ) -> tuple[dict[t.Any, t.Any], dict[t.Any, t.Any]]:
                    return _update_bidict_maps_impl(fwd, inv, items, on_dup.key.name, on_dup.val.name)

            if _update_bidict_maps_from_mapping_impl is None:
                update_bidict_maps_from_mapping = None
            else:

                def update_bidict_maps_from_mapping(
                    fwd: dict[t.Any, t.Any],
                    inv: dict[t.Any, t.Any],
                    mapping: Mapping[t.Any, t.Any],
                    on_dup: OnDup,
                ) -> tuple[dict[t.Any, t.Any], dict[t.Any, t.Any]]:
                    return _update_bidict_maps_from_mapping_impl(fwd, inv, mapping, on_dup.key.name, on_dup.val.name)

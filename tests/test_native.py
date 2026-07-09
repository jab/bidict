# Copyright 2009-2026 Joshua Bronson. All rights reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import annotations

import importlib
import sys
from collections.abc import Iterable
from types import SimpleNamespace

import pytest

from bidict import DROP_NEW
from bidict import ON_DUP_DROP_OLD
from bidict import RAISE
from bidict import KeyAndValueDuplicationError
from bidict import KeyDuplicationError
from bidict import OnDup
from bidict import OrderedBidict
from bidict import ValueDuplicationError
from bidict import _base as base_mod
from bidict import _native as native_mod
from bidict import bidict


def test_native_env_var_disables_helpers(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv('BIDICT_DISABLE_NATIVE', '1')
    reloaded = importlib.reload(native_mod)
    try:
        assert reloaded.build_bidict_maps is None
        assert reloaded.build_bidict_maps_from_mapping is None
        assert reloaded.update_bidict_maps is None
        assert reloaded.update_bidict_maps_from_mapping is None
    finally:
        monkeypatch.delenv('BIDICT_DISABLE_NATIVE', raising=False)
        importlib.reload(reloaded)


def test_non_cpython_runtime_disables_helpers(monkeypatch: pytest.MonkeyPatch) -> None:
    original_implementation = sys.implementation
    implementation_attrs = vars(original_implementation).copy()
    implementation_attrs['name'] = 'pypy'
    monkeypatch.setattr(sys, 'implementation', SimpleNamespace(**implementation_attrs))
    reloaded = importlib.reload(native_mod)
    try:
        assert reloaded.build_bidict_maps is None
        assert reloaded.build_bidict_maps_from_mapping is None
        assert reloaded.update_bidict_maps is None
        assert reloaded.update_bidict_maps_from_mapping is None
    finally:
        monkeypatch.setattr(sys, 'implementation', original_implementation)
        importlib.reload(reloaded)


def test_empty_update_uses_native_builder_when_available(monkeypatch: pytest.MonkeyPatch) -> None:
    items_seen: list[tuple[int, int]] = []

    def fake_build(items: Iterable[tuple[int, int]], _on_dup: object) -> tuple[dict[int, int], dict[int, int]]:
        items_seen.extend(items)
        return {1: 2}, {2: 1}

    monkeypatch.setattr(base_mod, '_build_bidict_maps', fake_build)
    bi = bidict[int, int]()

    bi.update([(1, 2)])

    assert items_seen == [(1, 2)]
    assert dict(bi.items()) == {1: 2}
    assert dict(bi.inverse.items()) == {2: 1}


def test_empty_mapping_update_uses_mapping_native_builder_when_available(monkeypatch: pytest.MonkeyPatch) -> None:
    seen_mapping: dict[int, int] | None = None

    def fail_build(_items: object, _on_dup: object) -> tuple[dict[int, int], dict[int, int]]:
        msg = 'generic native builder should not run for mapping updates'
        raise AssertionError(msg)

    def fake_build_from_mapping(mapping: dict[int, int], _on_dup: object) -> tuple[dict[int, int], dict[int, int]]:
        nonlocal seen_mapping
        seen_mapping = mapping
        return {1: 2}, {2: 1}

    monkeypatch.setattr(base_mod, '_build_bidict_maps', fail_build)
    monkeypatch.setattr(base_mod, '_build_bidict_maps_from_mapping', fake_build_from_mapping)
    bi = bidict[int, int]()

    mapping = {1: 2}
    bi.update(mapping)

    assert seen_mapping is mapping


def test_empty_mapping_update_prescans_early_dupvals_before_native_builder(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_build_from_mapping(_mapping: object, _on_dup: object) -> tuple[dict[int, int], dict[int, int]]:
        msg = 'native builder should not run after early duplicate-value prescan fails'
        raise AssertionError(msg)

    monkeypatch.setattr(base_mod, '_build_bidict_maps_from_mapping', fail_build_from_mapping)
    monkeypatch.setattr(base_mod, '_MAX_NATIVE_DUPVAL_FAST_FAIL_ITEMS', 2)
    bi = bidict[int, int]()

    with pytest.raises(ValueDuplicationError):
        bi.update({1: 0, 2: 0, 3: 3})

    assert not bi


def test_empty_update_preserves_materialized_inverse(monkeypatch: pytest.MonkeyPatch) -> None:
    items_seen: list[tuple[int, int]] = []
    bi = bidict[int, int]()
    inv = bi.inverse

    def fake_build(items: Iterable[tuple[int, int]], _on_dup: object) -> tuple[dict[int, int], dict[int, int]]:
        items_seen.extend(items)
        return {1: 2}, {2: 1}

    monkeypatch.setattr(base_mod, '_build_bidict_maps', fake_build)

    bi.update([(1, 2)])

    assert items_seen == [(1, 2)]
    assert dict(inv.items()) == {2: 1}
    assert inv.inverse is bi


def test_nonempty_update_skips_native_builder(monkeypatch: pytest.MonkeyPatch) -> None:
    bi = bidict({1: 2})

    def fail_build(_items: object, _on_dup: object) -> tuple[dict[int, int], dict[int, int]]:
        msg = 'native builder should not run for non-empty updates'
        raise AssertionError(msg)

    monkeypatch.setattr(base_mod, '_build_bidict_maps', fail_build)

    bi.update([(3, 4)])

    assert dict(bi.items()) == {1: 2, 3: 4}


def test_orderedbidict_skips_native_builder() -> None:
    bi = OrderedBidict([(1, 2), (3, 4)])

    assert not bi._supports_native_map_swap()
    assert tuple(bi.items()) == ((1, 2), (3, 4))


def test_nonempty_bulk_update_uses_native_updater_when_available(monkeypatch: pytest.MonkeyPatch) -> None:
    items_seen: list[tuple[int, int]] = []

    def fake_update(
        fwd: dict[int, int],
        inv: dict[int, int],
        items: Iterable[tuple[int, int]],
        _on_dup: object,
    ) -> tuple[dict[int, int], dict[int, int]]:
        items_seen.extend(items)
        assert fwd == {1: 2, 3: 4}
        assert inv == {2: 1, 4: 3}
        return {1: 2, 3: 4, 5: 6, 7: 8}, {2: 1, 4: 3, 6: 5, 8: 7}

    monkeypatch.setattr(base_mod, '_update_bidict_maps', fake_update)
    monkeypatch.setattr(base_mod, '_MIN_NATIVE_FORCEUPDATE_ITEMS', 2)
    bi = bidict({1: 2, 3: 4})

    bi.update([(5, 6), (7, 8)])

    assert items_seen == [(5, 6), (7, 8)]
    assert dict(bi.items()) == {1: 2, 3: 4, 5: 6, 7: 8}


def test_nonempty_mapping_update_uses_mapping_native_updater(monkeypatch: pytest.MonkeyPatch) -> None:
    seen_mapping: dict[int, int] | None = None

    def fail_update(
        _fwd: dict[int, int],
        _inv: dict[int, int],
        _items: Iterable[tuple[int, int]],
        _on_dup: object,
    ) -> tuple[dict[int, int], dict[int, int]]:
        msg = 'generic native updater should not run for mapping updates'
        raise AssertionError(msg)

    def fake_update_from_mapping(
        _fwd: dict[int, int],
        _inv: dict[int, int],
        mapping: dict[int, int],
        _on_dup: object,
    ) -> tuple[dict[int, int], dict[int, int]]:
        nonlocal seen_mapping
        seen_mapping = mapping
        return {1: 2, 3: 4, 5: 6, 7: 8}, {2: 1, 4: 3, 6: 5, 8: 7}

    monkeypatch.setattr(base_mod, '_update_bidict_maps', fail_update)
    monkeypatch.setattr(base_mod, '_update_bidict_maps_from_mapping', fake_update_from_mapping)
    monkeypatch.setattr(base_mod, '_MIN_NATIVE_UPDATE_ITEMS', 2)
    bi = bidict({1: 2, 3: 4})

    mapping = {5: 6, 7: 8}
    bi.update(mapping)

    assert seen_mapping is mapping


def test_nonempty_small_update_skips_native_updater(monkeypatch: pytest.MonkeyPatch) -> None:
    bi = bidict({1: 2, 3: 4})

    def fail_update(
        _fwd: object, _inv: object, _items: object, _on_dup: object
    ) -> tuple[dict[int, int], dict[int, int]]:
        msg = 'native updater should not run for small updates'
        raise AssertionError(msg)

    monkeypatch.setattr(base_mod, '_update_bidict_maps', fail_update)

    bi.update([(5, 6)])

    assert dict(bi.items()) == {1: 2, 3: 4, 5: 6}


def test_orderedbidict_skips_native_updater() -> None:
    bi = OrderedBidict({1: 2, 3: 4})
    assert not bi._supports_native_map_swap()


def test_forceupdate_uses_native_updater_when_available(monkeypatch: pytest.MonkeyPatch) -> None:
    items_seen: list[tuple[int, int]] = []

    def fake_update(
        fwd: dict[int, int],
        inv: dict[int, int],
        items: Iterable[tuple[int, int]],
        on_dup: object,
    ) -> tuple[dict[int, int], dict[int, int]]:
        items_seen.extend(items)
        assert fwd == {1: 2, 3: 4}
        assert inv == {2: 1, 4: 3}
        assert on_dup == ON_DUP_DROP_OLD
        return {1: 2, 5: 4, 6: 7}, {2: 1, 4: 5, 7: 6}

    monkeypatch.setattr(base_mod, '_update_bidict_maps', fake_update)
    monkeypatch.setattr(base_mod, '_MIN_NATIVE_UPDATE_ITEMS', 2)
    bi = bidict({1: 2, 3: 4})

    bi.forceupdate([(5, 4), (6, 7)])

    assert items_seen == [(5, 4), (6, 7)]
    assert dict(bi.items()) == {1: 2, 5: 4, 6: 7}


def test_nonempty_mapping_dupval_failure_uses_native_updater(monkeypatch: pytest.MonkeyPatch) -> None:
    called = False

    def fail_update(
        _fwd: object, _inv: object, _mapping: object, _on_dup: object
    ) -> tuple[dict[int, int], dict[int, int]]:
        nonlocal called
        called = True
        raise ValueDuplicationError(0)

    monkeypatch.setattr(base_mod, '_update_bidict_maps_from_mapping', fail_update)
    monkeypatch.setattr(base_mod, '_MIN_NATIVE_UPDATE_ITEMS', 1)
    bi = bidict({10: 10})

    with pytest.raises(ValueDuplicationError):
        bi.update({1: 0, 2: 0})

    assert called
    assert dict(bi.items()) == {10: 10}


def test_nonempty_mapping_update_preserves_duplication_precedence(monkeypatch: pytest.MonkeyPatch) -> None:
    called = False

    def fail_update(
        _fwd: object, _inv: object, _mapping: object, _on_dup: object
    ) -> tuple[dict[int, int], dict[int, int]]:
        nonlocal called
        called = True
        raise KeyDuplicationError(1)

    monkeypatch.setattr(base_mod, '_update_bidict_maps_from_mapping', fail_update)
    monkeypatch.setattr(base_mod, '_MIN_NATIVE_UPDATE_ITEMS', 1)
    bi = bidict({1: 10})

    with pytest.raises(KeyDuplicationError):
        bi.putall({1: 0, 2: 0, 3: 3}, OnDup(RAISE, RAISE))

    assert called
    assert dict(bi.items()) == {1: 10}


def test_nonempty_native_update_preserves_materialized_inverse(monkeypatch: pytest.MonkeyPatch) -> None:
    bi = bidict({1: 2, 3: 4})
    inv = bi.inverse

    def fake_update(
        _fwd: dict[int, int],
        _inv: dict[int, int],
        items: Iterable[tuple[int, int]],
        _on_dup: object,
    ) -> tuple[dict[int, int], dict[int, int]]:
        assert list(items) == [(3, 5), (6, 7)]
        return {1: 2, 3: 5, 6: 7}, {2: 1, 5: 3, 7: 6}

    monkeypatch.setattr(base_mod, '_update_bidict_maps', fake_update)
    monkeypatch.setattr(base_mod, '_MIN_NATIVE_UPDATE_ITEMS', 2)

    bi.update([(3, 5), (6, 7)])

    assert dict(inv.items()) == {2: 1, 5: 3, 7: 6}
    assert inv.inverse is bi


native_build = native_mod.build_bidict_maps
native_build_from_mapping = native_mod.build_bidict_maps_from_mapping
native_update = native_mod.update_bidict_maps
native_update_from_mapping = native_mod.update_bidict_maps_from_mapping
if (
    native_build is not None
    or native_build_from_mapping is not None
    or native_update is not None
    or native_update_from_mapping is not None
):
    pytest.importorskip('bidict_base_opt_native')


@pytest.mark.skipif(native_build is None, reason='optional native helper is not installed')
def test_native_build_bidict_maps_matches_drop_old_behavior() -> None:
    assert native_build is not None
    fwd, inv = native_build([(1, 2), (1, 3), (4, 3)], ON_DUP_DROP_OLD)

    assert fwd == {4: 3}
    assert inv == {3: 4}


@pytest.mark.skipif(native_build is None, reason='optional native helper is not installed')
def test_native_build_bidict_maps_honors_drop_new() -> None:
    assert native_build is not None
    on_dup = OnDup(key=DROP_NEW, val=DROP_NEW)
    fwd, inv = native_build([(1, 2), (1, 3), (4, 2)], on_dup)

    assert fwd == {1: 2}
    assert inv == {2: 1}


@pytest.mark.skipif(native_build is None, reason='optional native helper is not installed')
def test_native_build_bidict_maps_raises_value_duplication_error() -> None:
    assert native_build is not None
    with pytest.raises(ValueDuplicationError):
        native_build([(1, 2), (3, 2)], bidict.on_dup)


@pytest.mark.skipif(native_build is None, reason='optional native helper is not installed')
def test_native_build_bidict_maps_raises_key_and_value_duplication_error() -> None:
    assert native_build is not None
    with pytest.raises(KeyAndValueDuplicationError):
        native_build([(1, 2), (3, 4), (1, 4)], bidict.on_dup)


@pytest.mark.skipif(native_build_from_mapping is None, reason='optional native mapping helper is not installed')
def test_native_build_bidict_maps_from_mapping_matches_drop_old_behavior() -> None:
    assert native_build_from_mapping is not None
    fwd, inv = native_build_from_mapping({1: 3, 4: 3}, ON_DUP_DROP_OLD)

    assert fwd == {4: 3}
    assert inv == {3: 4}


@pytest.mark.skipif(native_update is None, reason='optional native helper is not installed')
def test_native_update_bidict_maps_matches_drop_old_behavior() -> None:
    assert native_update is not None
    fwd = {1: 2, 3: 4}
    inv = {2: 1, 4: 3}

    new_fwd, new_inv = native_update(fwd, inv, [(3, 5), (6, 5)], ON_DUP_DROP_OLD)

    assert new_fwd == {1: 2, 6: 5}
    assert new_inv == {2: 1, 5: 6}
    assert fwd == {1: 2, 3: 4}
    assert inv == {2: 1, 4: 3}


@pytest.mark.skipif(native_update is None, reason='optional native helper is not installed')
def test_native_update_bidict_maps_raises_without_mutating_inputs() -> None:
    assert native_update is not None
    fwd = {1: 2, 3: 4}
    inv = {2: 1, 4: 3}

    with pytest.raises(ValueDuplicationError):
        native_update(fwd, inv, [(5, 6), (7, 4)], bidict.on_dup)

    assert fwd == {1: 2, 3: 4}
    assert inv == {2: 1, 4: 3}


@pytest.mark.skipif(native_update_from_mapping is None, reason='optional native mapping helper is not installed')
def test_native_update_bidict_maps_from_mapping_matches_drop_old_behavior() -> None:
    assert native_update_from_mapping is not None
    fwd = {1: 2, 3: 4}
    inv = {2: 1, 4: 3}

    new_fwd, new_inv = native_update_from_mapping(fwd, inv, {3: 5, 6: 5}, ON_DUP_DROP_OLD)

    assert new_fwd == {1: 2, 6: 5}
    assert new_inv == {2: 1, 5: 6}
    assert fwd == {1: 2, 3: 4}
    assert inv == {2: 1, 4: 3}

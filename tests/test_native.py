# Copyright 2009-2026 Joshua Bronson. All rights reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import annotations

from collections.abc import Iterable

import pytest

from bidict import DROP_NEW
from bidict import ON_DUP_DROP_OLD
from bidict import KeyAndValueDuplicationError
from bidict import OnDup
from bidict import ValueDuplicationError
from bidict import _base as base_mod
from bidict import _native as native_mod
from bidict import bidict


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


def test_nonempty_update_skips_native_builder(monkeypatch: pytest.MonkeyPatch) -> None:
    bi = bidict({1: 2})

    def fail_build(_items: object, _on_dup: object) -> tuple[dict[int, int], dict[int, int]]:
        msg = 'native builder should not run for non-empty updates'
        raise AssertionError(msg)

    monkeypatch.setattr(base_mod, '_build_bidict_maps', fail_build)

    bi.update([(3, 4)])

    assert dict(bi.items()) == {1: 2, 3: 4}


native_build = native_mod.build_bidict_maps
if native_build is not None:
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

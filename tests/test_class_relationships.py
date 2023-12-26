# Copyright 2009-2023 Joshua Bronson. All rights reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Test various issubclass checks."""

from __future__ import annotations

import typing as t
from collections import OrderedDict
from collections.abc import Hashable
from collections.abc import Mapping
from collections.abc import MutableMapping
from collections.abc import Reversible

import pytest

from bidict import BidictBase
from bidict import BidirectionalMapping
from bidict import MutableBidict
from bidict import MutableBidirectionalMapping
from bidict import OrderedBidict
from bidict import OrderedBidictBase
from bidict import bidict
from bidict import frozenbidict


class AbstractBimap(BidirectionalMapping[t.Any, t.Any]):
    """Does not override `inverse` and therefore should not be instantiatable."""


BiT: t.TypeAlias = t.Type[BidictBase[t.Any, t.Any]]

BIDICT_BASE_TYPES: tuple[BiT, ...] = (BidictBase, MutableBidict, OrderedBidictBase)
BIDICT_TYPES = (*BIDICT_BASE_TYPES, bidict, frozenbidict, OrderedBidict)
BIMAP_TYPES = (*BIDICT_TYPES, AbstractBimap)
NOT_BIMAP_TYPES = (dict, OrderedDict, int, object)
MUTABLE_BIDICT_TYPES = (bidict, OrderedBidict)
HASHABLE_BIDICT_TYPES = (frozenbidict,)
ORDERED_BIDICT_TYPES = (OrderedBidict,)


@pytest.mark.parametrize('bi_cls', BIMAP_TYPES)
def test_issubclass_bimap(bi_cls: BiT) -> None:
    """All bidict types should be considered subclasses of :class:`BidirectionalMapping`."""
    assert issubclass(bi_cls, BidirectionalMapping)


@pytest.mark.parametrize('not_bi_cls', NOT_BIMAP_TYPES)
def test_not_issubclass_not_bimap(not_bi_cls: t.Any) -> None:
    """Classes that do not conform to :class:`BidirectionalMapping` interface
    should not be considered subclasses of it.
    """
    assert not issubclass(not_bi_cls, BidirectionalMapping)


@pytest.mark.parametrize('bi_cls', BIDICT_TYPES)
def test_issubclass_mapping(bi_cls: BiT) -> None:
    """All bidict types should be :class:`collections.abc.Mapping`s."""
    assert issubclass(bi_cls, Mapping)


@pytest.mark.parametrize('bi_cls', MUTABLE_BIDICT_TYPES)
def test_issubclass_mutable_and_mutable_bidirectional_mapping(bi_cls: BiT) -> None:
    """All mutable bidict types should be mutable (bidirectional) mappings."""
    assert issubclass(bi_cls, MutableMapping)
    assert issubclass(bi_cls, MutableBidirectionalMapping)


@pytest.mark.parametrize('bi_cls', HASHABLE_BIDICT_TYPES)
def test_hashable_not_mutable(bi_cls: BiT) -> None:
    """All hashable bidict types should not be mutable (bidirectional) mappings."""
    assert not issubclass(bi_cls, MutableMapping)
    assert not issubclass(bi_cls, MutableBidirectionalMapping)


@pytest.mark.parametrize('bi_cls', HASHABLE_BIDICT_TYPES)
def test_issubclass_hashable(bi_cls: BiT) -> None:
    """All hashable bidict types should implement :class:`collections.abc.Hashable`."""
    assert issubclass(bi_cls, Hashable)


@pytest.mark.parametrize('bi_cls', BIDICT_TYPES)
def test_reversible(bi_cls: BiT) -> None:
    """All built-in bidict types should be reversible."""
    assert issubclass(bi_cls, Reversible)


def test_issubclass_internal() -> None:
    """The docs specifically recommend using ABCs
    over concrete classes when checking whether an interface is provided
    (see :ref:`polymorphism`).

    The relationships tested here are not guaranteed to hold in the future,
    but are still tested so that any unintentional changes won't go unnoticed.
    """
    assert not issubclass(bidict, OrderedBidict)
    assert not issubclass(bidict, frozenbidict)

    assert not issubclass(OrderedBidict, bidict)
    assert not issubclass(OrderedBidict, frozenbidict)

    assert not issubclass(frozenbidict, OrderedBidict)
    assert not issubclass(frozenbidict, bidict)

    # Regression test for #111, Bug in BidirectionalMapping.__subclasshook__():
    # Any class with an inverse attribute is considered a collections.abc.Mapping
    OnlyHasInverse = type('OnlyHasInverse', (), {'inverse': 'foo'})
    assert not issubclass(OnlyHasInverse, Mapping)


def test_abstract_bimap_init_fails() -> None:
    """Instantiating `AbstractBimap` should fail with expected TypeError."""
    excmatch = "Can't instantiate abstract class AbstractBimap"
    with pytest.raises(TypeError, match=excmatch):
        AbstractBimap()  # type: ignore [abstract]


def test_bimap_inverse_notimplemented() -> None:
    """Calling .inverse on a BidirectionalMapping should raise :class:`NotImplementedError`."""
    with pytest.raises(NotImplementedError):
        # Can't instantiate a BidirectionalMapping that hasn't overridden the abstract methods of
        # the interface, so only way to call this implementation is on the class.
        BidirectionalMapping.inverse.fget(bidict())  # type: ignore [attr-defined]


@pytest.mark.parametrize('bi_cls', BIDICT_BASE_TYPES)
def test_bidict_bases_init_succeed(bi_cls: BiT) -> None:
    """Bidict base classes should be initializable and have a working .inverse property."""
    b = bi_cls(one=1, two=2)
    assert dict(b.inverse) == {1: 'one', 2: 'two'}

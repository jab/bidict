# -*- coding: utf-8 -*-
# Copyright 2018 Joshua Bronson. All Rights Reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Test various issubclass checks."""

import pytest

from bidict import bidict, frozenbidict, FrozenOrderedBidict, OrderedBidict, BidirectionalMapping
from bidict.compat import Mapping, MutableMapping, Hashable


class OldStyleClass:  # pylint: disable=old-style-class,no-init,too-few-public-methods
    """In Python 2 this is an old-style class (not derived from object)."""


class VirtualBimapSubclass(Mapping):  # pylint: disable=abstract-method
    """Dummy type that implements the BidirectionalMapping interface
    without explicitly extending it, and so should still be considered a
    (virtual) subclass if the BidirectionalMapping ABC is working correctly.
    (See :meth:`bidict.BidirectionalMapping.__subclasshook__`.)

    (Not actually a *working* BidirectionalMapping implementation,
    but doesn't need to be for the purposes of this test.)
    """

    inv = NotImplemented


class AbstractBimap(BidirectionalMapping):  # pylint: disable=abstract-method
    """Dummy type that explicitly extends BidirectionalMapping
    but fails to provide a concrete implementation for the
    :attr:`BidirectionalMapping.inv` :func:`abc.abstractproperty`.

    As a result, attempting to create an instance of this class
    should result in ``TypeError: Can't instantiate abstract class
    AbstractBimap with abstract methods inv``
    """

    __getitem__ = NotImplemented
    __iter__ = NotImplemented
    __len__ = NotImplemented


BIDICT_TYPES = (bidict, frozenbidict, FrozenOrderedBidict, OrderedBidict)
BIMAP_TYPES = BIDICT_TYPES + (VirtualBimapSubclass, AbstractBimap)
NOT_BIMAP_TYPES = (dict, object, OldStyleClass)
MUTABLE_BIDICT_TYPES = (bidict, OrderedBidict)
HASHABLE_BIDICT_TYPES = (frozenbidict, FrozenOrderedBidict)
ORDERED_BIDICT_TYPES = (OrderedBidict, FrozenOrderedBidict)


@pytest.mark.parametrize('cls', BIMAP_TYPES + NOT_BIMAP_TYPES)
def test_issubclass_bimap(cls):
    """Ensure all bidict types are :class:`bidict.BidirectionalMapping`s,
    as well as VirtualBimapSubclass (via __subclasshook__).
    """
    is_bimap = issubclass(cls, BidirectionalMapping)
    assert cls in BIMAP_TYPES if is_bimap else NOT_BIMAP_TYPES


@pytest.mark.parametrize('bi_cls', BIDICT_TYPES)
def test_issubclass_mapping(bi_cls):
    """Ensure all bidict types are :class:`collections.abc.Mapping`s."""
    assert issubclass(bi_cls, Mapping)


@pytest.mark.parametrize('bi_cls', MUTABLE_BIDICT_TYPES)
def test_issubclass_mutablemapping(bi_cls):
    """Ensure all mutable bidict types are :class:`collections.abc.MutableMapping`s."""
    assert issubclass(bi_cls, MutableMapping)


@pytest.mark.parametrize('bi_cls', HASHABLE_BIDICT_TYPES)
def test_issubclass_hashable(bi_cls):
    """Ensure all hashable bidict types implement :class:`collections.abc.Hashable`."""
    assert issubclass(bi_cls, Hashable)


@pytest.mark.parametrize('bi_cls', ORDERED_BIDICT_TYPES)
def test_ordered_reversible(bi_cls):
    """Ensure all ordered bidict types are reversible."""
    assert callable(bi_cls.__reversed__)


def test_issubclass_internal():
    """The docs specifically recommend using ABCs
    over concrete classes when checking whether an interface is provided
    (see :ref:`polymorphism`).
    The relationships tested here are not guaranteed to hold in the future,
    but are still tested so that any unintentional changes won't go unnoticed.
    """
    assert issubclass(OrderedBidict, bidict)
    assert not issubclass(frozenbidict, bidict)
    assert not issubclass(FrozenOrderedBidict, bidict)

    assert not issubclass(bidict, frozenbidict)
    assert not issubclass(OrderedBidict, FrozenOrderedBidict)

    assert not issubclass(FrozenOrderedBidict, frozenbidict)
    assert not issubclass(FrozenOrderedBidict, OrderedBidict)


def test_abstract_bimap_init_fails():
    """See the :class:`AbstractBimap` docstring above."""
    with pytest.raises(TypeError):
        AbstractBimap()  # pylint: disable=abstract-class-instantiated

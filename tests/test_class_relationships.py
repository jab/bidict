# -*- coding: utf-8 -*-
# Copyright 2009-2020 Joshua Bronson. All Rights Reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Test various issubclass checks."""

import re
from collections.abc import Hashable, Mapping, MutableMapping
from collections import OrderedDict

import pytest

from bidict import (
    bidict, frozenbidict, FrozenOrderedBidict, OrderedBidict, BidirectionalMapping, MutableBidirectionalMapping)


class AbstractBimap(BidirectionalMapping):  # pylint: disable=abstract-method
    """Dummy type that explicitly extends BidirectionalMapping
    but fails to override the :attr:`BidirectionalMapping.inverse`
    :func:`abc.abstractproperty`.

    As a result, attempting to create an instance of this class
    should result in ``TypeError: Can't instantiate abstract class
    AbstractBimap with abstract methods inverse``
    """


BIDICT_TYPES = (bidict, frozenbidict, FrozenOrderedBidict, OrderedBidict)
BIMAP_TYPES = BIDICT_TYPES + (AbstractBimap,)
NOT_BIMAP_TYPES = (dict, OrderedDict, int, object)
MUTABLE_BIDICT_TYPES = (bidict, OrderedBidict)
HASHABLE_BIDICT_TYPES = (frozenbidict, FrozenOrderedBidict)
ORDERED_BIDICT_TYPES = (OrderedBidict, FrozenOrderedBidict)


@pytest.mark.parametrize('bi_cls', BIMAP_TYPES)
def test_issubclass_bimap(bi_cls):
    """All bidict types should be considered subclasses of :class:`BidirectionalMapping`."""
    assert issubclass(bi_cls, BidirectionalMapping)


@pytest.mark.parametrize('not_bi_cls', NOT_BIMAP_TYPES)
def test_not_issubclass_not_bimap(not_bi_cls):
    """Classes that do not conform to :class:`BidirectionalMapping` interface
    should not be considered subclasses of it.
    """
    assert not issubclass(not_bi_cls, BidirectionalMapping)


@pytest.mark.parametrize('bi_cls', BIDICT_TYPES)
def test_issubclass_mapping(bi_cls):
    """All bidict types should be :class:`collections.abc.Mapping`s."""
    assert issubclass(bi_cls, Mapping)


@pytest.mark.parametrize('bi_cls', MUTABLE_BIDICT_TYPES)
def test_issubclass_mutable_and_mutable_bidirectional_mapping(bi_cls):
    """All mutable bidict types should be mutable (bidirectional) mappings."""
    assert issubclass(bi_cls, MutableMapping)
    assert issubclass(bi_cls, MutableBidirectionalMapping)


@pytest.mark.parametrize('bi_cls', HASHABLE_BIDICT_TYPES)
def test_hashable_not_mutable(bi_cls):
    """All hashable bidict types should not be mutable (bidirectional) mappings."""
    assert not issubclass(bi_cls, MutableMapping)
    assert not issubclass(bi_cls, MutableBidirectionalMapping)


@pytest.mark.parametrize('bi_cls', HASHABLE_BIDICT_TYPES)
def test_issubclass_hashable(bi_cls):
    """All hashable bidict types should implement :class:`collections.abc.Hashable`."""
    assert issubclass(bi_cls, Hashable)


@pytest.mark.parametrize('bi_cls', ORDERED_BIDICT_TYPES)
def test_ordered_reversible(bi_cls):
    """All ordered bidict types should be reversible."""
    assert callable(bi_cls.__reversed__)


def test_issubclass_internal():
    """The docs specifically recommend using ABCs
    over concrete classes when checking whether an interface is provided
    (see :ref:`polymorphism`).

    The relationships tested here are not guaranteed to hold in the future,
    but are still tested so that any unintentional changes won't go unnoticed.
    """
    assert not issubclass(bidict, FrozenOrderedBidict)
    assert not issubclass(bidict, OrderedBidict)
    assert not issubclass(bidict, frozenbidict)

    assert not issubclass(FrozenOrderedBidict, OrderedBidict)
    assert not issubclass(FrozenOrderedBidict, bidict)
    assert not issubclass(FrozenOrderedBidict, frozenbidict)

    assert not issubclass(OrderedBidict, FrozenOrderedBidict)
    assert not issubclass(OrderedBidict, bidict)
    assert not issubclass(OrderedBidict, frozenbidict)

    assert not issubclass(frozenbidict, FrozenOrderedBidict)
    assert not issubclass(frozenbidict, OrderedBidict)
    assert not issubclass(frozenbidict, bidict)

    # Regression test for #111, Bug in BidirectionalMapping.__subclasshook__():
    # Any class with an inverse attribute is considered a collections.abc.Mapping
    OnlyHasInverse = type('OnlyHasInverse', (), {'inverse': ...})
    assert not issubclass(OnlyHasInverse, Mapping)


def test_abstract_bimap_init_fails():
    """See the :class:`AbstractBimap` docstring above."""
    with pytest.raises(TypeError) as excinfo:
        AbstractBimap()  # pylint: disable=abstract-class-instantiated
    assert re.search(
        "Can't instantiate abstract class AbstractBimap with abstract methods .* inverse",
        str(excinfo.value))


def test_bimap_inverse_notimplemented():
    """Calling .inverse on a BidirectionalMapping should raise :class:`NotImplementedError`."""
    with pytest.raises(NotImplementedError):
        # Can't instantiate a BidirectionalMapping that hasn't overridden the abstract methods of
        # the interface, so only way to call this implementation is on the class.
        BidirectionalMapping.inverse.fget(bidict())

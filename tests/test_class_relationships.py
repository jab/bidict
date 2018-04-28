# -*- coding: utf-8 -*-
# Copyright 2018 Joshua Bronson. All Rights Reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Test various issubclass checks."""

from collections import Hashable

import pytest

from bidict import bidict, frozenbidict, FrozenOrderedBidict, OrderedBidict, BidirectionalMapping
from bidict.compat import Mapping, MutableMapping, PY2


class OldStyleClass:  # pylint: disable=old-style-class,no-init,too-few-public-methods
    """In Python 2 this is an old-style class (not derived from object)."""


class VirtualBimapSubclass(Mapping):  # pylint: disable=abstract-method
    """Dummy type that implements the BidirectionalMapping interface
    without explicitly extending it, and so should still be considered a
    (virtual) subclass if the BidirectionalMapping ABC is working correctly.
    (See :meth:`BidirectionalMapping.__subclasshook__`.)

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


@pytest.mark.parametrize('bi_cls', BIMAP_TYPES)
def test_issubclass_bimap(bi_cls):
    """All bidict types should subclass :class:`BidirectionalMapping`,
    and any class conforming to the interface (e.g. VirtualBimapSubclass)
    should be considered a (virtual) subclass too.
    """
    assert issubclass(bi_cls, BidirectionalMapping)


@pytest.mark.parametrize('not_bi_cls', NOT_BIMAP_TYPES)
def test_not_issubclass_not_bimap(not_bi_cls):
    """Classes that do not conform to :class:`BidirectionalMapping`
    should not be considered subclasses.
    """
    assert not issubclass(not_bi_cls, BidirectionalMapping)
    # Make sure one of the types tested is an old-style class on Python 2,
    # i.e. that BidirectionalMapping.__subclasshook__ doesn't break for them.
    if PY2:  # testing the tests ¯\_(ツ)_/¯
        assert any(not issubclass(cls, object) for cls in NOT_BIMAP_TYPES)


@pytest.mark.parametrize('bi_cls', BIDICT_TYPES)
def test_issubclass_mapping(bi_cls):
    """All bidict types should be :class:`collections.abc.Mapping`s."""
    assert issubclass(bi_cls, Mapping)


@pytest.mark.parametrize('bi_cls', MUTABLE_BIDICT_TYPES)
def test_issubclass_mutablemapping(bi_cls):
    """All mutable bidict types should be :class:`collections.abc.MutableMapping`s."""
    assert issubclass(bi_cls, MutableMapping)


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
    assert not issubclass(OrderedBidict, bidict)
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


def test_bimap_inv_notimplemented():
    """Calling .inv on a BidirectionalMapping should raise :class:`NotImplementedError`."""
    with pytest.raises(NotImplementedError):
        # Can't instantiate a BidirectionalMapping that hasn't overridden the abstract methods of
        # the interface, so only way to call this implementation is on the class.
        BidirectionalMapping.inv.fget(bidict())  # pylint: disable=no-member

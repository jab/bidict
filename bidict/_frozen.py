# -*- coding: utf-8 -*-
# Copyright 2017 Joshua Bronson. All Rights Reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Implements the frozen (immutable, hashable) bidict types."""

from collections import ItemsView

from ._common import BidictBase
from ._ordered import OrderedBidictBase


class FrozenBidict(BidictBase):  # lgtm [py/missing-equals]
    """
    Regular frozen bidict type.

    Provides a default implementation of :meth:`compute_hash`
    that uses ``ItemsView._hash()`` to compute the hash in constant space.
    Override :meth:`compute_hash` if you require a different implementation.

    (For example, you could create an ephemeral :py:class:`frozenset`
    from the contained items and pass that to :func:`hash`.
    This would take linear space, but on CPython, it results in the faster
    ``frozenset_hash`` routine defined in ``setobject.c`` being used.)
    """

    def compute_hash(self):
        """
        Use the pure Python implementation of Python's frozenset hashing
        algorithm from ``collections.Set._hash`` to compute the hash
        incrementally in constant space.

        """
        return ItemsView(self)._hash()  # pylint: disable=protected-access

    def __hash__(self):
        """
        Return the hash of this frozen bidict from its contained items.

        Delegates to :attr:`compute_hash` on the first call,
        then caches the result to make future calls *O(1)*.
        """
        if hasattr(self, '_hash'):  # Cached on the first call.
            return self._hash  # pylint: disable=access-member-before-definition
        self._hash = self.compute_hash()  # pylint: disable=attribute-defined-outside-init
        return self._hash


class FrozenOrderedBidict(OrderedBidictBase, FrozenBidict):  # lgtm [py/missing-equals]
    r"""Ordered frozen bidict type.

    Inherits :class:`FrozenBidict`\'s
    :attr:`compute_hash <FrozenBidict.compute_hash>`
    implementation.

    This causes two :class:`FrozenOrderedBidict`\s with the same items
    in different order to get the same hash value even though they are unequal,
    leading to more hash collisions when inserting them into a set or mapping.
    However, this is necessary because a :class:`FrozenOrderedBidict` and a
    :class:`FrozenBidict` with the same items should compare equal, and so
    they must also hash to the same value.
    """

    # __hash__ must be set explicitly, will not be inherited from base class.
    __hash__ = FrozenBidict.__hash__

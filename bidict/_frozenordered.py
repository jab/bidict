# -*- coding: utf-8 -*-
# Copyright 2018 Joshua Bronson. All Rights Reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


#==============================================================================
#                    * Welcome to the bidict source code *
#==============================================================================

# Doing a code review? You'll find a "Code review nav" comment like the one
# below at the top and bottom of the most important source files. This provides
# a suggested path through the source while you're still getting familiar.
#
# Note: If you aren't reading this on https://github.com/jab/bidict, you may be
# viewing an outdated version of the code. Please head to GitHub to review the
# latest version, which contains important improvements over older versions.
#
# Thank you for reading and for any feedback you provide.

#                             * Code review nav *
#==============================================================================
#  ← Prev: _ordered.py     Current: _frozenordered.py                   <FIN>
#==============================================================================

"""Provides :class:`FrozenOrderedBidict`, an immutable, hashable, ordered bidict type."""

from ._frozen import frozenbidict
from ._ordered import OrderedBidictBase


# FrozenOrderedBidict intentionally does not subclass frozenbidict because it only complicates the
# inheritance hierarchy without providing any actual code reuse: The only thing from frozenbidict
# that FrozenOrderedBidict uses is frozenbidict.__hash__(), but Python specifically prevents
# __hash__ from being inherited; it must instead always be set explicitly as below. Users seeking
# some `is_frozenbidict(..)` test that succeeds for both frozenbidicts and FrozenOrderedBidicts
# should therefore not use isinstance(foo, frozenbidict), but should instead use the appropriate
# ABCs, e.g. `isinstance(foo, BidirectionalMapping) and not isinstance(foo, MutableMapping)`.
class FrozenOrderedBidict(OrderedBidictBase):  # lgtm [py/missing-equals]
    """Frozen (i.e. hashable, immutable) ordered bidict."""

    __slots__ = ()

    # frozenbidict.__hash__ is also correct for ordered bidicts:
    # The value is derived from all contained items and insensitive to their order.
    # If an ordered bidict "O" is equal to a mapping, its unordered counterpart "U" is too.
    # Since U1 == U2 => hash(U1) == hash(U2), then if O == U1, hash(O) must equal hash(U1).

    __hash__ = frozenbidict.__hash__  # Must set explicitly, __hash__ is never inherited.


#                             * Code review nav *
#==============================================================================
#  ← Prev: _ordered.py     Current: _frozenordered.py                   <FIN>
#==============================================================================

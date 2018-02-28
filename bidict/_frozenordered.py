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
#  ← Prev: _orderedbase.py  Current: _frozenordered.py    Next: _ordered.py →
#==============================================================================

"""Provides :class:`FrozenOrderedBidict`, an immutable, hashable, ordered bidict."""

from ._frozen import frozenbidict
from ._orderedbase import OrderedBidictBase
from .compat import PY2


# FrozenOrderedBidict intentionally does not subclass frozenbidict because it only complicates the
# inheritance hierarchy without providing any actual code reuse: The only thing from frozenbidict
# that FrozenOrderedBidict uses is frozenbidict.__hash__(), but Python specifically prevents
# __hash__ from being inherited; it must instead always be defined explicitly as below. Users who
# need an `is_frozenbidict(..)` test that succeeds for both frozenbidicts and FrozenOrderedBidicts
# should therefore not use isinstance(foo, frozenbidict), but should instead use the appropriate
# ABCs, e.g. `isinstance(foo, BidirectionalMapping) and not isinstance(foo, MutableMapping)`.
class FrozenOrderedBidict(OrderedBidictBase):
    """Hashable, immutable, ordered bidict type."""

    __slots__ = ()

    # frozenbidict.__hash__ can be resued for FrozenOrderedBidict:
    # FrozenOrderedBidict inherits BidictBase.__eq__ which is order-insensitive,
    # and frozenbidict.__hash__ is consistent with BidictBase.__eq__.
    __hash__ = frozenbidict.__hash__  # Must define __hash__ explicitly, Python prevents inheriting
    if PY2:
        # Must grab the __func__ attribute off the method in Python 2, or else get "TypeError:
        # unbound method __hash__() must be called with frozenbidict instance as first argument"
        __hash__ = __hash__.__func__


#                             * Code review nav *
#==============================================================================
#  ← Prev: _orderedbase.py  Current: _frozenordered.py    Next: _ordered.py →
#==============================================================================

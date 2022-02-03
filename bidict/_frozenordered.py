# Copyright 2009-2022 Joshua Bronson. All Rights Reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


#==============================================================================
#                    * Welcome to the bidict source code *
#==============================================================================

# Doing a code review? You'll find a "Code review nav" comment like the one
# below at the top and bottom of the most important source files. This provides
# a suggested initial path through the source when reviewing.
#
# Note: If you aren't reading this on https://github.com/jab/bidict, you may be
# viewing an outdated version of the code. Please head to GitHub to review the
# latest version, which contains important improvements over older versions.
#
# Thank you for reading and for any feedback you provide.

#                             * Code review nav *
#==============================================================================
#← Prev: _orderedbase.py  Current: _frozenordered.py  Next: _orderedbidict.py →
#==============================================================================

"""Provide :class:`FrozenOrderedBidict`, an immutable, hashable, ordered bidict."""

import typing as t

from ._base import BidictBase
from ._frozenbidict import frozenbidict
from ._orderedbase import OrderedBidictBase
from ._typing import KT, VT


class FrozenOrderedBidict(OrderedBidictBase[KT, VT]):
    """Hashable, immutable, ordered bidict type.

    Like a hashable :class:`bidict.OrderedBidict`
    without the mutating APIs, or like a
    reversible :class:`bidict.frozenbidict` even on Python < 3.8.
    (All bidicts are order-preserving when never mutated, so frozenbidict is
    already order-preserving, but only on Python 3.8+, where dicts are
    reversible, are all bidicts (including frozenbidict) also reversible.)

    If you are using Python 3.8+, frozenbidict gives you everything that
    FrozenOrderedBidict gives you, but with less space overhead.
    On the other hand, using FrozenOrderedBidict when you are depending on
    the ordering of the items can make the ordering dependence more explicit.
    """

    __hash__: t.Callable[[t.Any], int] = frozenbidict.__hash__

    if t.TYPE_CHECKING:
        @property
        def inverse(self) -> 'FrozenOrderedBidict[VT, KT]': ...

    # Use BidictBase's implementations of the following methods, which delegate
    # to the _fwdm/_invm dicts for more efficient implementations of these mapping views
    # compared to those used by the implementations inherited from OrderedBidictBase.
    # This is possible with FrozenOrderedBidict since it is immutable, i.e. mutations that
    # could change the initial ordering (e.g. requiring a less efficient __iter__ implementation)
    # are not supported.
    keys = BidictBase.keys
    values = BidictBase.values
    items = BidictBase.items


#                             * Code review nav *
#==============================================================================
#← Prev: _orderedbase.py  Current: _frozenordered.py  Next: _orderedbidict.py →
#==============================================================================

# -*- coding: utf-8 -*-
# Copyright 2009-2020 Joshua Bronson. All Rights Reserved.
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

"""Provides :class:`FrozenOrderedBidict`, an immutable, hashable, ordered bidict."""

from ._frozenbidict import frozenbidict
from ._orderedbase import OrderedBidictBase
from .compat import DICTS_ORDERED


class FrozenOrderedBidict(OrderedBidictBase):
    """Hashable, immutable, ordered bidict type."""

    __slots__ = ()
    __hash__ = frozenbidict.__hash__

    # If the Python implementation's dict type is ordered (e.g. PyPy or CPython >= 3.6), then we can
    # delegate to `_fwdm` and `_invm` for faster implementations of several methods. Both `_fwdm`
    # and `_invm` will always be initialized with the provided items in the correct order, and since
    # `FrozenOrderedBidict` is immutable, their respective orders can't get out of sync after a
    # mutation.
    if DICTS_ORDERED:
        def __iter__(self, reverse=False):  # noqa: N802
            """Iterator over the contained items."""
            if reverse:
                return super().__iter__(reverse=True)
            return iter(self._fwdm._fwdm)  # pylint: disable=protected-access

        def keys(self):
            """A set-like object providing a view on the contained keys."""
            return self._fwdm._fwdm.keys()  # pylint: disable=protected-access

        def values(self):
            """A set-like object providing a view on the contained values."""
            return self._invm._fwdm.keys()  # pylint: disable=protected-access

        # We can't delegate for items because values in `_fwdm` are nodes.


#                             * Code review nav *
#==============================================================================
#← Prev: _orderedbase.py  Current: _frozenordered.py  Next: _orderedbidict.py →
#==============================================================================

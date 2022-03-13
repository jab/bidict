# Copyright 2009-2022 Joshua Bronson. All rights reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


#                             * Code review nav *
#                        (see comments in __init__.py)
#==============================================================================
# ← Prev: _base.py          Current: _frozenbidict.py       Next: _bidict.py →
#==============================================================================

"""Provide :class:`frozenbidict`, an immutable, hashable bidirectional mapping type."""

import typing as t

from ._base import BidictBase
from ._typing import KT, VT


class frozenbidict(BidictBase[KT, VT]):
    """Immutable, hashable bidict type."""

    _hash: int

    # Work around lack of support for higher-kinded types in Python.
    # Ref: https://github.com/python/typing/issues/548#issuecomment-621571821
    if t.TYPE_CHECKING:
        @property
        def inverse(self) -> 'frozenbidict[VT, KT]': ...

    def __hash__(self) -> int:
        """The hash of this bidict as determined by its items."""
        if getattr(self, '_hash', None) is None:
            # The following is like hash(frozenset(self.items()))
            # but more memory efficient. See also: https://bugs.python.org/issue46684
            self._hash = t.ItemsView(self)._hash()  # type: ignore [attr-defined]  # https://github.com/python/typeshed/pull/7153
        return self._hash


#                             * Code review nav *
#==============================================================================
# ← Prev: _base.py          Current: _frozenbidict.py       Next: _bidict.py →
#==============================================================================

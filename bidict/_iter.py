# Copyright 2009-2022 Joshua Bronson. All Rights Reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


"""Functions for iterating over items in a mapping."""

import typing as t
from collections.abc import Mapping
from itertools import chain
from operator import itemgetter

from ._typing import KT, VT, IterItems, MapOrIterItems


def iteritems_mapping_or_iterable(arg: MapOrIterItems[KT, VT]) -> IterItems[KT, VT]:
    """Yield the items in *arg*.

    If *arg* is a :class:`~collections.abc.Mapping`, return an iterator over its items.
    Otherwise return an iterator over *arg* itself.
    """
    return iter(arg.items() if isinstance(arg, Mapping) else arg)


def iteritems(arg: MapOrIterItems[KT, VT], **kw: VT) -> IterItems[KT, VT]:
    """Yield the items from *arg* and then any from *kw* in the order given."""
    it: IterItems[t.Any, VT] = iter(())
    if arg:
        it = iteritems_mapping_or_iterable(arg)
    if kw:
        iterkw = iter(kw.items())
        it = chain(it, iterkw)
    return it


swap = itemgetter(1, 0)


def inverted(arg: MapOrIterItems[KT, VT]) -> IterItems[VT, KT]:
    """Yield the inverse items of the provided object.

    If *arg* has a :func:`callable` ``__inverted__`` attribute,
    return the result of calling it.

    Otherwise, return an iterator over the items in `arg`,
    inverting each item on the fly.

    *See also* :attr:`bidict.BidirectionalMapping.__inverted__`
    """
    invattr = getattr(arg, '__inverted__', None)
    if callable(invattr):
        inv: IterItems[VT, KT] = invattr()
        return inv
    return map(swap, iteritems_mapping_or_iterable(arg))

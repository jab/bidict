# -*- coding: utf-8 -*-
# Copyright 2018 Joshua Bronson. All Rights Reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


"""Provides :class:`_ProxiedKeysVals` and :class:`_ProxiedKeysValsItems."""

from .compat import PY2


class _ProxiedKeysVals(object):
    r"""Mixin providing more efficient implementations
    of :meth:`keys` and :meth:`values`
    (as well as their iter\* and view\* counterparts on Python 2)
    by proxying calls through to the backing dicts so they run at native speed,
    compared to the implementations from :class:`collections.abc.Mapping`.

    Similar functionality for :meth:`items` is moved
    into the :class:`_ProxiedKeysValsItems` subclass below
    so that :class:`FrozenOrderedBidict` can benefit from using just this mixin;
    the :meth:`_ProxiedKeysValsItems.items` implementation below
    is not useful for :class:`FrozenOrderedBidict`.
    """

    __slots__ = ()

    # pylint: disable=no-member

    def keys(self):
        """A set-like object providing a view on the contained keys."""
        return self._fwdm.keys()

    def values(self):
        """A set-like object providing a view on the contained values.

        Note that because the values of a :class:`~bidict.BidirectionalMapping`
        are the keys of its inverse,
        this returns a :class:`~collections.abc.KeysView`
        rather than a :class:`~collections.abc.ValuesView`,
        which has the advantages of constant-time containment checks
        and supporting set operations.
        """
        return self._invm.keys()

    if PY2:
        def viewkeys(self):  # pylint: disable=missing-docstring
            return self._fwdm.viewkeys()

        viewkeys.__doc__ = keys.__doc__
        keys.__doc__ = 'A list of the contained keys.'

        def viewvalues(self):  # pylint: disable=missing-docstring
            return self._invm.viewkeys()

        viewvalues.__doc__ = values.__doc__
        values.__doc__ = 'A list of the contained values.'

        def iterkeys(self):
            """An iterator over the contained keys."""
            return self._fwdm.iterkeys()

        def itervalues(self):
            """An iterator over the contained values."""
            return self._invm.iterkeys()


class _ProxiedKeysValsItems(_ProxiedKeysVals):
    r"""Extend :class:`_ProxiedKeysVals` with
    a similarly-more-efficient implementation of :meth:`items`
    (as well as its iter\* and view\* counterparts on Python 2).
    """

    __slots__ = ()

    # pylint: disable=no-member

    def items(self):
        """A set-like object providing a view on the contained items."""
        return self._fwdm.items()

    if PY2:
        def viewitems(self):  # pylint: disable=missing-docstring
            return self._fwdm.viewitems()

        viewitems.__doc__ = items.__doc__
        items.__doc__ = 'A list of the contained items.'

        def iteritems(self):
            """An iterator over the contained items."""
            return self._fwdm.iteritems()

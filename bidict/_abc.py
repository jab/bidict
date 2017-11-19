# -*- coding: utf-8 -*-
# Copyright 2017 Joshua Bronson. All Rights Reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Provides bidict ABCs."""

from collections import Mapping

from .compat import iteritems


class BidirectionalMapping(Mapping):  # pylint: disable=abstract-method
    """Abstract base class for bidirectional mappings.
    Extends :class:`collections.abc.Mapping`.

    .. py:attribute:: inv

        The inverse mapping.

    .. py:attribute:: _subclsattrs

        The attributes that :attr:`__subclasshook__` checks for to determine
        whether a class is a subclass of :class:`BidirectionalMapping`.
    """

    __slots__ = ()

    inv = NotImplemented

    def __inverted__(self):
        """Get an iterator over the items in :attr:`inv`."""
        return iteritems(self.inv)

    _subclsattrs = frozenset({
        'inv', '__inverted__',
        # see "Mapping" in the table at
        # https://docs.python.org/3/library/collections.abc.html#collections-abstract-base-classes
        '__getitem__', '__iter__', '__len__',  # abstract methods
        '__contains__', 'keys', 'items', 'values', 'get', '__eq__', '__ne__',  # mixin methods
    })

    @classmethod
    def __subclasshook__(cls, C):  # noqa: N803 ("argument name should be lowercase")
        # Standard to use "C" for this arg in __subclasshook__, e.g.:
        # https://github.com/python/cpython/blob/d505a2/Lib/_collections_abc.py#L93
        """Check if C provides all the attributes in :attr:`_subclsattrs`.

        Causes conforming classes to be virtual subclasses automatically.
        """
        if cls is not BidirectionalMapping:  # lgtm [py/comparison-using-is]
            return NotImplemented
        mro = getattr(C, '__mro__', None)
        if mro is None:
            return NotImplemented
        return all(any(B.__dict__.get(i) for B in mro) for i in cls._subclsattrs)

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
#  ← Prev: __init__.py         Current: _abc.py            Next: _frozen.py →
#==============================================================================


"""Provides the :class:`BidirectionalMapping` abstract base class."""

from collections import Mapping

from .compat import iteritems


class BidirectionalMapping(Mapping):  # pylint: disable=abstract-method,no-init
    """Abstract base class (ABC) for bidirectional mapping types.

    Extends :class:`collections.abc.Mapping` primarily by adding the :attr:`inv`
    attribute, which holds a reference to the inverse mapping.

    Implements :attr:`__subclasshook__` such that any
    :class:`~collections.abc.Mapping` that also provides an
    :attr:`~BidirectionalMapping.inv` implementation
    will be considered a (virtual) subclass of this ABC.
    """

    __slots__ = ()

    #: The inverse bidirectional mapping.
    #: Defaults to :obj:`NotImplemented`,
    #: meant to be overridden by concrete subclasses.
    #: See also :attr:`bidict.frozenbidict.inv`
    inv = NotImplemented

    def __inverted__(self):
        """Get an iterator over the items in :attr:`inv`.

        This is functionally equivalent to iterating over the items in the
        forward mapping and inverting each one on the fly, but this provides a
        more efficient implementation: Assuming the already-inverted items
        are stored in :attr:`inv`, just return an iterator over them directly.

        Providing this default implementation enables external functions,
        particularly :func:`~bidict.inverted`, to use this optimized
        implementation when available, instead of having to invert on the fly.
        See also :func:`bidict.inverted`
        """
        return iteritems(self.inv)

    #: The attributes that :attr:`__subclasshook__` checks for to determine
    #: whether a class is a subclass of :class:`BidirectionalMapping`.
    _subclsattrs = frozenset({
        # (__inverted__ not included, as it's an optimization, not a requirement of the interface)
        'inv',
        # The following are all the methods provided by the `collections.abc.Mapping` interface.
        # See "Mapping" in the table at
        # https://docs.python.org/3/library/collections.abc.html#collections-abstract-base-classes
        '__getitem__', '__iter__', '__len__',  # abstract methods
        '__contains__', 'keys', 'items', 'values', 'get', '__eq__', '__ne__',  # mixin methods
    })

    @classmethod
    def __subclasshook__(cls, C):  # noqa: N803 "argument name should be lowercase" -
        # "C" is the standard name for this arg in __subclasshook__ implementations, see e.g.
        # https://github.com/python/cpython/blob/d505a2/Lib/_collections_abc.py#L93
        """Check if *C* provides all the attributes in :attr:`_subclsattrs`.

        Causes conforming classes to be virtual subclasses automatically.
        """
        if cls is not BidirectionalMapping:  # lgtm [py/comparison-using-is]
            return NotImplemented
        mro = getattr(C, '__mro__', None)
        if mro is None:
            return NotImplemented
        return all(any(B.__dict__.get(i) for B in mro) for i in cls._subclsattrs)


#                             * Code review nav *
#==============================================================================
#  ← Prev: __init__.py         Current: _abc.py            Next: _frozen.py →
#==============================================================================

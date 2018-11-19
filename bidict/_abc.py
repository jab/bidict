# -*- coding: utf-8 -*-
# Copyright 2009-2018 Joshua Bronson. All Rights Reserved.
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
#  ← Prev: __init__.py         Current: _abc.py              Next: _base.py →
#==============================================================================


"""Provides the :class:`BidirectionalMapping` abstract base class."""

from .compat import Mapping, abstractproperty, iteritems


class BidirectionalMapping(Mapping):  # pylint: disable=abstract-method,no-init
    """Abstract base class (ABC) for bidirectional mapping types.

    Extends :class:`collections.abc.Mapping` primarily by adding the
    (abstract) :attr:`inv` property,
    which implementors of :class:`BidirectionalMapping`
    should override to return a reference to the inverse
    :class:`BidirectionalMapping` instance.

    Implements :attr:`__subclasshook__` such that any
    :class:`~collections.abc.Mapping` that also provides
    :attr:`~BidirectionalMapping.inv`
    will be considered a (virtual) subclass of this ABC.
    """

    __slots__ = ()

    @abstractproperty
    def inv(self):
        """The inverse of this bidirectional mapping instance.

        *See also* :attr:`bidict.BidictBase.inv`

        :raises NotImplementedError: Meant to be overridden in subclasses.
        """
        # The @abstractproperty decorator prevents BidirectionalMapping subclasses from being
        # instantiated unless they override this method. So users shouldn't be able to get to the
        # point where they can unintentionally call this implementation of .inv on something
        # anyway. Could leave the method body empty, but raise NotImplementedError so it's extra
        # clear there's no reason to call this implementation (e.g. via super() after overriding).
        raise NotImplementedError

    def __inverted__(self):
        """Get an iterator over the items in :attr:`inv`.

        This is functionally equivalent to iterating over the items in the
        forward mapping and inverting each one on the fly, but this provides a
        more efficient implementation: Assuming the already-inverted items
        are stored in :attr:`inv`, just return an iterator over them directly.

        Providing this default implementation enables external functions,
        particularly :func:`~bidict.inverted`, to use this optimized
        implementation when available, instead of having to invert on the fly.

        *See also* :func:`bidict.inverted`
        """
        return iteritems(self.inv)

    @classmethod
    def __subclasshook__(cls, C):  # noqa: N803 (argument name should be lowercase)
        """Check if *C* is a :class:`~collections.abc.Mapping`
        that also provides an ``inv`` attribute,
        thus conforming to the :class:`BidirectionalMapping` interface,
        in which case it will be considered a (virtual) C
        even if it doesn't explicitly extend it.
        """
        if cls is not BidirectionalMapping:  # lgtm [py/comparison-using-is]
            return NotImplemented
        if not Mapping.__subclasshook__(C):
            return NotImplemented
        mro = getattr(C, '__mro__', None)
        if mro is None:  # Python 2 old-style class
            return NotImplemented
        if not any(B.__dict__.get('inv') for B in mro):
            return NotImplemented
        return True


#                             * Code review nav *
#==============================================================================
#  ← Prev: __init__.py         Current: _abc.py              Next: _base.py →
#==============================================================================

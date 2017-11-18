# Copyright 2017 Joshua Bronson. All Rights Reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Provides ABCs, DuplicationBehaviors, and BidictExceptions."""

from abc import abstractproperty
from collections import Mapping

from .compat import iteritems


class BidirectionalMapping(Mapping):
    """Abstract base class for bidirectional mappings.
    Extends :class:`collections.abc.Mapping`.

    .. py:attribute:: _subclsattrs

        The attributes that :attr:`__subclasshook__` checks for to determine
        whether a class is a subclass of :class:`BidirectionalMapping`.
    """

    __slots__ = ()

    @abstractproperty
    def inv(self):
        """The inverse bidict."""

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


class _Marker(object):
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return '<%s>' % self.name  # pragma: no cover


class DuplicationBehavior(_Marker):
    """
    Provide RAISE, OVERWRITE, IGNORE, and ON_DUP_VAL duplication behaviors.

    .. py:attribute:: RAISE

        Raise an exception when a duplication is encountered.

    .. py:attribute:: OVERWRITE

        Overwrite an existing item when a duplication is encountered.

    .. py:attribute:: IGNORE

        Keep the existing item and ignore the new item when a duplication is
        encountered.

    .. py:attribute:: ON_DUP_VAL

        Used with *on_dup_kv* to specify that it should match whatever the
        duplication behavior of *on_dup_val* is.
    """


DuplicationBehavior.RAISE = RAISE = DuplicationBehavior('RAISE')
DuplicationBehavior.OVERWRITE = OVERWRITE = DuplicationBehavior('OVERWRITE')
DuplicationBehavior.IGNORE = IGNORE = DuplicationBehavior('IGNORE')
DuplicationBehavior.ON_DUP_VAL = ON_DUP_VAL = DuplicationBehavior('ON_DUP_VAL')
_MISS = _Marker('MISSING')


class BidictException(Exception):
    """Base class for bidict exceptions."""


class DuplicationError(BidictException):
    """Base class for exceptions raised when uniqueness is violated."""


class KeyDuplicationError(DuplicationError):
    """Raised when a given key is not unique."""


class ValueDuplicationError(DuplicationError):
    """Raised when a given value is not unique."""


class KeyAndValueDuplicationError(KeyDuplicationError, ValueDuplicationError):
    """
    Raised when a given item's key and value are not unique.

    That is, its key duplicates that of another item,
    and its value duplicates that of a different other item.
    """

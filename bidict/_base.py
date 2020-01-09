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
# ← Prev: _abc.py             Current: _base.py   Next:     _frozenbidict.py →
#==============================================================================


"""Provides :class:`BidictBase`."""

from collections import namedtuple
from collections.abc import Mapping
from copy import copy
from functools import wraps
from warnings import warn
from weakref import ref

from ._abc import BidirectionalMapping
from ._dup import ON_DUP_DEFAULT, RAISE, DROP_OLD, DROP_NEW, OnDup
from ._exc import (
    DuplicationError, KeyDuplicationError, ValueDuplicationError, KeyAndValueDuplicationError)
from ._sntl import _MISS, _NOOP
from ._util import _iteritems_args_kw


_DedupResult = namedtuple('_DedupResult', 'isdupkey isdupval invbyval fwdbykey')
_WriteResult = namedtuple('_WriteResult', 'key val oldkey oldval')
_NODUP = _DedupResult(False, False, _MISS, _MISS)


# TODO: Remove this compatibility decorator in a future release. pylint: disable=fixme
def _on_dup_compat(__init__):
    deprecated = ('on_dup_key', 'on_dup_val', 'on_dup_kv')
    msg = 'The `on_dup_key`, `on_dup_val`, and `on_dup_kv` class attrs are deprecated and ' \
          'will be removed in a future version of bidict. Use the `on_dup` class attr instead.'

    @wraps(__init__)
    def wrapper(self, *args, **kw):
        cls = self.__class__
        shim = {s[len('on_dup_'):]: getattr(cls, s) for s in deprecated if hasattr(cls, s)}
        if shim:
            warn(msg, stacklevel=2)
            cls.on_dup = OnDup(**shim)
        return __init__(self, *args, **kw)

    return wrapper


# Since BidirectionalMapping implements __subclasshook__, and BidictBase
# provides all the required attributes that the __subclasshook__ checks for,
# BidictBase would be a (virtual) subclass of BidirectionalMapping even if
# it didn't subclass it explicitly. But subclassing BidirectionalMapping
# explicitly allows BidictBase to inherit any useful implementations that
# BidirectionalMapping provides that aren't part of the required interface,
# such as its implementations of `__inverted__` and `values`.

class BidictBase(BidirectionalMapping):
    """Base class implementing :class:`BidirectionalMapping`."""

    __slots__ = ('_fwdm', '_invm', '_inv', '_invweak', '_hash', '__weakref__')

    #: The default :class:`~bidict.OnDup`
    #: that governs behavior when a provided item
    #: duplicates the key or value of other item(s).
    #:
    #: *See also* :ref:`basic-usage:Values Must Be Unique`, :doc:`extending`
    on_dup = ON_DUP_DEFAULT

    _fwdm_cls = dict
    _invm_cls = dict

    #: The object used by :meth:`__repr__` for printing the contained items.
    _repr_delegate = dict

    @_on_dup_compat
    def __init__(self, *args, **kw):  # pylint: disable=super-init-not-called
        """Make a new bidirectional dictionary.
        The signature behaves like that of :class:`dict`.
        Items passed in are added in the order they are passed,
        respecting the :attr:`on_dup` class attribute in the process.
        """
        #: The backing :class:`~collections.abc.Mapping`
        #: storing the forward mapping data (*key* → *value*).
        self._fwdm = self._fwdm_cls()
        #: The backing :class:`~collections.abc.Mapping`
        #: storing the inverse mapping data (*value* → *key*).
        self._invm = self._invm_cls()
        self._init_inv()  # lgtm [py/init-calls-subclass]
        if args or kw:
            self._update(True, self.on_dup, *args, **kw)

    def _init_inv(self):
        # Compute the type for this bidict's inverse bidict (will be different from this
        # bidict's type if _fwdm_cls and _invm_cls are different).
        inv_cls = self._inv_cls()
        # Create the inverse bidict instance via __new__, bypassing its __init__ so that its
        # _fwdm and _invm can be assigned to this bidict's _invm and _fwdm. Store it in self._inv,
        # which holds a strong reference to a bidict's inverse, if one is available.
        self._inv = inv = inv_cls.__new__(inv_cls)
        inv._fwdm = self._invm  # pylint: disable=protected-access
        inv._invm = self._fwdm  # pylint: disable=protected-access
        # Only give the inverse a weak reference to this bidict to avoid creating a reference cycle,
        # stored in the _invweak attribute. See also the docs in
        # :ref:`addendum:Bidict Avoids Reference Cycles`
        inv._inv = None  # pylint: disable=protected-access
        inv._invweak = ref(self)  # pylint: disable=protected-access
        # Since this bidict has a strong reference to its inverse already, set its _invweak to None.
        self._invweak = None

    @classmethod
    def _inv_cls(cls):
        """The inverse of this bidict type, i.e. one with *_fwdm_cls* and *_invm_cls* swapped."""
        if cls._fwdm_cls is cls._invm_cls:
            return cls
        if not getattr(cls, '_inv_cls_', None):
            class _Inv(cls):
                _fwdm_cls = cls._invm_cls
                _invm_cls = cls._fwdm_cls
                _inv_cls_ = cls
            _Inv.__name__ = cls.__name__ + 'Inv'
            cls._inv_cls_ = _Inv
        return cls._inv_cls_

    @property
    def _isinv(self):
        return self._inv is None

    @property
    def inverse(self):
        """The inverse of this bidict.

        *See also* :attr:`inv`
        """
        # Resolve and return a strong reference to the inverse bidict.
        # One may be stored in self._inv already.
        if self._inv is not None:
            return self._inv
        # Otherwise a weakref is stored in self._invweak. Try to get a strong ref from it.
        inv = self._invweak()  # pylint: disable=not-callable
        if inv is not None:
            return inv
        # Refcount of referent must have dropped to zero, as in `bidict().inv.inv`. Init a new one.
        self._init_inv()  # Now this bidict will retain a strong ref to its inverse.
        return self._inv

    @property
    def inv(self):
        """Alias for :attr:`inverse`."""
        return self.inverse

    def __getstate__(self):
        """Needed to enable pickling due to use of :attr:`__slots__` and weakrefs.

        *See also* :meth:`object.__getstate__`
        """
        state = {}
        for cls in self.__class__.__mro__:
            slots = getattr(cls, '__slots__', ())
            for slot in slots:
                if hasattr(self, slot):
                    state[slot] = getattr(self, slot)
        # weakrefs can't be pickled.
        state.pop('_invweak', None)  # Added back in __setstate__ via _init_inv call.
        state.pop('__weakref__', None)  # Not added back in __setstate__. Python manages this one.
        return state

    def __setstate__(self, state):
        """Implemented because use of :attr:`__slots__` would prevent unpickling otherwise.

        *See also* :meth:`object.__setstate__`
        """
        for slot, value in state.items():
            setattr(self, slot, value)
        self._init_inv()

    def __repr__(self):
        """See :func:`repr`."""
        clsname = self.__class__.__name__
        if not self:
            return '%s()' % clsname
        return '%s(%r)' % (clsname, self._repr_delegate(self.items()))

    # The inherited Mapping.__eq__ implementation would work, but it's implemented in terms of an
    # inefficient ``dict(self.items()) == dict(other.items())`` comparison, so override it with a
    # more efficient implementation.
    def __eq__(self, other):
        """*x.__eq__(other)　⟺　x == other*

        Equivalent to *dict(x.items()) == dict(other.items())*
        but more efficient.

        Note that :meth:`bidict's __eq__() <bidict.bidict.__eq__>` implementation
        is inherited by subclasses,
        in particular by the ordered bidict subclasses,
        so even with ordered bidicts,
        :ref:`== comparison is order-insensitive <eq-order-insensitive>`.

        *See also* :meth:`bidict.FrozenOrderedBidict.equals_order_sensitive`
        """
        if not isinstance(other, Mapping) or len(self) != len(other):
            return False
        selfget = self.get
        return all(selfget(k, _MISS) == v for (k, v) in other.items())

    # The following methods are mutating and so are not public. But they are implemented in this
    # non-mutable base class (rather than the mutable `bidict` subclass) because they are used here
    # during initialization (starting with the `_update` method). (Why is this? Because `__init__`
    # and `update` share a lot of the same behavior (inserting the provided items while respecting
    # `on_dup`), so it makes sense for them to share implementation too.)
    def _pop(self, key):
        val = self._fwdm.pop(key)
        del self._invm[val]
        return val

    def _put(self, key, val, on_dup):
        dedup_result = self._dedup_item(key, val, on_dup)
        if dedup_result is not _NOOP:
            self._write_item(key, val, dedup_result)

    def _dedup_item(self, key, val, on_dup):  # pylint: disable=too-many-branches
        """Check *key* and *val* for any duplication in self.

        Handle any duplication as per the passed in *on_dup*.

        (key, val) already present is construed as a no-op, not a duplication.

        If duplication is found and the corresponding :class:`~bidict.OnDupAction` is
        :attr:`~bidict.DROP_NEW`, return :obj:`_NOOP`.

        If duplication is found and the corresponding :class:`~bidict.OnDupAction` is
        :attr:`~bidict.RAISE`, raise the appropriate error.

        If duplication is found and the corresponding :class:`~bidict.OnDupAction` is
        :attr:`~bidict.DROP_OLD`,
        or if no duplication is found,
        return the :class:`_DedupResult` *(isdupkey, isdupval, oldkey, oldval)*.
        """
        fwdm = self._fwdm
        invm = self._invm
        oldval = fwdm.get(key, _MISS)
        oldkey = invm.get(val, _MISS)
        isdupkey = oldval is not _MISS
        isdupval = oldkey is not _MISS
        dedup_result = _DedupResult(isdupkey, isdupval, oldkey, oldval)
        if isdupkey and isdupval:
            if self._already_have(key, val, oldkey, oldval):
                # (key, val) duplicates an existing item -> no-op.
                return _NOOP
            # key and val each duplicate a different existing item.
            if on_dup.kv is RAISE:
                raise KeyAndValueDuplicationError(key, val)
            if on_dup.kv is DROP_NEW:
                return _NOOP
            if on_dup.kv is not DROP_OLD:  # pragma: no cover
                raise ValueError(on_dup.kv)
            # Fall through to the return statement on the last line.
        elif isdupkey:
            if on_dup.key is RAISE:
                raise KeyDuplicationError(key)
            if on_dup.key is DROP_NEW:
                return _NOOP
            if on_dup.key is not DROP_OLD:  # pragma: no cover
                raise ValueError(on_dup.key)
            # Fall through to the return statement on the last line.
        elif isdupval:
            if on_dup.val is RAISE:
                raise ValueDuplicationError(val)
            if on_dup.val is DROP_NEW:
                return _NOOP
            if on_dup.val is not DROP_OLD:  # pragma: no cover
                raise ValueError(on_dup.val)
            # Fall through to the return statement on the last line.
        # else neither isdupkey nor isdupval.
        return dedup_result

    @staticmethod
    def _already_have(key, val, oldkey, oldval):
        # Overridden by _orderedbase.OrderedBidictBase.
        isdup = oldkey == key
        assert isdup == (oldval == val), '%r %r %r %r' % (key, val, oldkey, oldval)
        return isdup

    def _write_item(self, key, val, dedup_result):
        # Overridden by _orderedbase.OrderedBidictBase.
        isdupkey, isdupval, oldkey, oldval = dedup_result
        fwdm = self._fwdm
        invm = self._invm
        fwdm[key] = val
        invm[val] = key
        if isdupkey:
            del invm[oldval]
        if isdupval:
            del fwdm[oldkey]
        return _WriteResult(key, val, oldkey, oldval)

    def _update(self, init, on_dup, *args, **kw):
        # args[0] may be a generator that yields many items, so process input in a single pass.
        if not args and not kw:
            return
        can_skip_dup_check = not self and not kw and isinstance(args[0], BidirectionalMapping)
        if can_skip_dup_check:
            self._update_no_dup_check(args[0])
            return
        can_skip_rollback = init or RAISE not in on_dup
        if can_skip_rollback:
            self._update_no_rollback(on_dup, *args, **kw)
        else:
            self._update_with_rollback(on_dup, *args, **kw)

    def _update_no_dup_check(self, other):
        write_item = self._write_item
        for (key, val) in other.items():
            write_item(key, val, _NODUP)

    def _update_no_rollback(self, on_dup, *args, **kw):
        put = self._put
        for (key, val) in _iteritems_args_kw(*args, **kw):
            put(key, val, on_dup)

    def _update_with_rollback(self, on_dup, *args, **kw):
        """Update, rolling back on failure."""
        writelog = []
        appendlog = writelog.append
        dedup_item = self._dedup_item
        write_item = self._write_item
        for (key, val) in _iteritems_args_kw(*args, **kw):
            try:
                dedup_result = dedup_item(key, val, on_dup)
            except DuplicationError:
                undo_write = self._undo_write
                for dedup_result, write_result in reversed(writelog):
                    undo_write(dedup_result, write_result)
                raise
            if dedup_result is not _NOOP:
                write_result = write_item(key, val, dedup_result)
                appendlog((dedup_result, write_result))

    def _undo_write(self, dedup_result, write_result):
        isdupkey, isdupval, _, _ = dedup_result
        key, val, oldkey, oldval = write_result
        if not isdupkey and not isdupval:
            self._pop(key)
            return
        fwdm = self._fwdm
        invm = self._invm
        if isdupkey:
            fwdm[key] = oldval
            invm[oldval] = key
            if not isdupval:
                del invm[val]
        if isdupval:
            invm[val] = oldkey
            fwdm[oldkey] = val
            if not isdupkey:
                del fwdm[key]

    def copy(self):
        """A shallow copy."""
        # Could just ``return self.__class__(self)`` here instead, but the below is faster. It uses
        # __new__ to create a copy instance while bypassing its __init__, which would result
        # in copying this bidict's items into the copy instance one at a time. Instead, make whole
        # copies of each of the backing mappings, and make them the backing mappings of the copy,
        # avoiding copying items one at a time.
        cp = self.__class__.__new__(self.__class__)  # pylint: disable=invalid-name
        cp._fwdm = copy(self._fwdm)  # pylint: disable=protected-access
        cp._invm = copy(self._invm)  # pylint: disable=protected-access
        cp._init_inv()  # pylint: disable=protected-access
        return cp

    def __copy__(self):
        """Used for the copy protocol.

        *See also* the :mod:`copy` module
        """
        return self.copy()

    def __len__(self):
        """The number of contained items."""
        return len(self._fwdm)

    def __iter__(self):  # lgtm [py/inheritance/incorrect-overridden-signature]
        """Iterator over the contained items."""
        # No default implementation for __iter__ inherited from Mapping ->
        # always delegate to _fwdm.
        return iter(self._fwdm)

    def __getitem__(self, key):
        """*x.__getitem__(key)　⟺　x[key]*"""
        return self._fwdm[key]

#                             * Code review nav *
#==============================================================================
# ← Prev: _abc.py             Current: _base.py   Next:     _frozenbidict.py →
#==============================================================================

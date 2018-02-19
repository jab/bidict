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

#==============================================================================
#  ← Prev: _abc.py           * Code review nav *           Next: _bidict.py →
#==============================================================================


"""Implements :class:`frozenbidict`, the base class for all other bidict types."""

from collections import ItemsView, Mapping
from weakref import ref

from ._abc import BidirectionalMapping
from ._dup import RAISE, OVERWRITE, IGNORE
from ._exc import (
    DuplicationError, KeyDuplicationError, ValueDuplicationError, KeyAndValueDuplicationError)
from ._miss import _MISS
from .compat import PY2, iteritems
from .util import pairs


# Since BidirectionalMapping implements __subclasshook__, and frozenbidict
# provides all the required attributes that the __subclasshook__ checks for,
# frozenbidict would be a (virtual) subclass of BidirectionalMapping even if
# it didn't subclass it explicitly. But subclassing BidirectionalMapping
# explicitly allows frozenbidict to inherit any useful methods that
# BidirectionalMapping provides that aren't part of the required interface,
# such as its optimized __inverted__ implementation.

# pylint: disable=invalid-name
class frozenbidict(BidirectionalMapping):  # noqa: N801
    u"""
    Immutable, hashable bidict type.

    Also serves as a base class for the other bidict types.

    .. py:attribute:: on_dup_key

        The default :class:`DuplicationPolicy` used in the event that an item
        duplicates only the key of another item,
        when a policy has not been specified explicitly
        (e.g. the policy used by
        :meth:`~bidict.bidict.__setitem__` and
        :meth:`~bidict.bidict.update`).
        Defaults to :attr:`~DuplicationPolicy.OVERWRITE`
        to match :class:`dict`'s behavior.

        See also :ref:`extending`

    .. py:attribute:: on_dup_val

        The default :class:`DuplicationPolicy` used in the event that an item
        duplicates only the value of another item,
        when a policy has not been specified explicitly
        (e.g. the policy used by
        :meth:`~bidict.bidict.__setitem__` and
        :meth:`~bidict.bidict.update`).
        Defaults to :attr:`~DuplicationPolicy.RAISE`
        to prevent unintended overwrite of another item.

        See also :ref:`extending`

    .. py:attribute:: on_dup_kv

        The default :class:`DuplicationPolicy` used in the event that an item
        duplicates the key of another item and the value of yet another item,
        when a policy has not been specified explicitly
        (e.g. the policy used by
        :meth:`~bidict.bidict.__setitem__` and
        :meth:`~bidict.bidict.update`).
        Defaults to ``None``, which causes the *on_dup_kv* policy to match
        whatever *on_dup_val* policy is in effect.

        See also :ref:`extending`

    .. py:attribute:: fwdm

        The backing :class:`~collections.abc.Mapping`
        storing the forward mapping data (*key* → *value*).

    .. py:attribute:: invm

        The backing :class:`~collections.abc.Mapping`
        storing the inverse mapping data (*value* → *key*).

    .. py:attribute:: fwdm_cls

        The :class:`~collections.abc.Mapping` type
        used for the backing :attr:`fwdm` mapping,
        Defaults to :class:`dict`.
        Override this if you need different behavior.

        See also :ref:`extending`

    .. py:attribute:: invm_cls

        The :class:`~collections.abc.Mapping` type
        used for the backing :attr:`invm` mapping.
        Defaults to :class:`dict`.
        Override this if you need different behavior.

        See also :ref:`extending`
    """

    __slots__ = ['fwdm', 'invm', '_inv', '_invref', '_hash']

    if not PY2:
        __slots__.append('__weakref__')

    on_dup_key = OVERWRITE
    on_dup_val = RAISE
    on_dup_kv = None
    fwdm_cls = dict
    invm_cls = dict

    def __init__(self, *args, **kw):  # pylint: disable=super-init-not-called
        """Make a new bidirectional dictionary.
        The signature is the same as that of regular dictionaries.
        Items passed in are added in the order they are passed,
        respecting this bidict type's duplication policies along the way.
        See also :attr:`on_dup_key`, :attr:`on_dup_val`, :attr:`on_dup_kv`
        """
        self.fwdm = self.fwdm_cls()
        self.invm = self.invm_cls()
        self._init_inv()  # lgtm [py/init-calls-subclass]
        if args or kw:
            self._update(True, self.on_dup_key, self.on_dup_val, self.on_dup_kv, *args, **kw)

    @classmethod
    def inv_cls(cls):
        """The inverse of this bidict type, i.e. one with *fwdm_cls* and *invm_cls* swapped."""
        if cls.fwdm_cls is cls.invm_cls:
            return cls
        if not getattr(cls, '_inv_cls', None):
            class _Inv(cls):
                fwdm_cls = cls.invm_cls
                invm_cls = cls.fwdm_cls
                inv_cls = cls
            _Inv.__name__ = cls.__name__ + 'Inv'
            cls._inv_cls = _Inv
        return cls._inv_cls

    def _init_inv(self):
        self._inv = inv = object.__new__(self.inv_cls())
        inv.fwdm = self.invm
        inv.invm = self.fwdm
        inv._invref = ref(self)  # pylint: disable=protected-access
        inv._inv = self._invref = None  # pylint: disable=protected-access

    @property
    def _isinv(self):
        return self._inv is None

    @property
    def inv(self):
        """The inverse of this bidict."""
        if self._inv is not None:
            return self._inv
        inv = self._invref()  # pylint: disable=E1102
        if inv is not None:
            return inv
        # Refcount of referent must have dropped to zero, as in `bidict().inv.inv`. Init a new one.
        self._init_inv()
        return self._inv

    def __getstate__(self):
        state = {}
        for cls in self.__class__.__mro__:
            slots = getattr(cls, '__slots__', ())
            for slot in slots:
                if hasattr(self, slot):
                    state[slot] = getattr(self, slot)
        state['__weakref__'] = None
        state['_invref'] = None
        return state

    def __setstate__(self, state):
        for slot, value in iteritems(state):
            if slot == '__weakref__':
                continue
            setattr(self, slot, value)

    def __repr__(self):
        """See :func:`repr`."""
        clsname = self.__class__.__name__
        if not self:
            return '%s()' % clsname
        return '%s(%r)' % (clsname, self.__repr_delegate__())

    def __repr_delegate__(self):
        """The object used by :attr:`__repr__` to represent the contained items."""
        return self.fwdm

    def __hash__(self):
        """The hash of this bidict as determined by its items."""
        if getattr(self, '_hash', None) is None:  # pylint: disable=protected-access
            # pylint: disable=protected-access,attribute-defined-outside-init
            self._hash = ItemsView(self)._hash()
        return self._hash

    # The inherited Mapping.__eq__ implementation would work, but it's implemented in terms of an
    # inefficient ``dict(self.items()) == dict(other.items())`` comparison, so override it with a
    # more efficient implementation.
    def __eq__(self, other):
        """``x.__eq__(other) <==> x == other``

        Equivalent to ``dict(x.items()) == dict(other.items())``
        but more efficient.

        Note this implementation of ``__eq__`` is inherited by subclasses of
        this class, in particular by the ordered bidict subclasses, so ``==``
        comparison is always order-insensitive.
        See also :meth:`bidict.FrozenOrderedBidict.equals_order_sensitive`
        """
        if not isinstance(other, Mapping) or len(self) != len(other):
            return False
        selfget = self.get
        return all(selfget(k, _MISS) == v for (k, v) in iteritems(other))

    # The following methods mutate frozenbidicts and so are not public. But they are implemented in
    # this immutable class (rather than the mutable `bidict` subclass) because they are used here
    # during initialization (starting with the `_update` method). (Why is this? Because `__init__`
    # and `update` share a lot of the same behavior (inserting the provided items while respecting
    # the active duplication policies), so it makes sense for them to share implementation too.)
    def _pop(self, key):
        val = self.fwdm.pop(key)
        del self.invm[val]
        return val

    def _put(self, key, val, on_dup_key, on_dup_val, on_dup_kv):
        dedup_result = self._dedup_item(key, val, on_dup_key, on_dup_val, on_dup_kv)
        if dedup_result:
            self._write_item(key, val, *dedup_result)

    def _dedup_item(self, key, val, on_dup_key, on_dup_val, on_dup_kv):
        """
        Check *key* and *val* for any duplication in self.

        Handle any duplication as per the given duplication policies.

        (key, val) already present is construed as a no-op, not a duplication.

        If duplication is found and the corresponding duplication policy is
        :attr:`~bidict.DuplicationPolicy.RAISE`, raise the appropriate error.

        If duplication is found and the corresponding duplication policy is
        :attr:`~bidict.DuplicationPolicy.IGNORE`, return *None*.

        If duplication is found and the corresponding duplication policy is
        :attr:`~bidict.DuplicationPolicy.OVERWRITE`,
        or if no duplication is found,
        return the dedup result
        *(isdupkey, isdupval, invbyval, fwdbykey)*.
        """
        if on_dup_kv is None:
            on_dup_kv = on_dup_val
        fwdm = self.fwdm
        invm = self.invm
        fwdbykey = fwdm.get(key, _MISS)
        invbyval = invm.get(val, _MISS)
        isdupkey = fwdbykey is not _MISS
        isdupval = invbyval is not _MISS
        if isdupkey and isdupval:
            if self._isdupitem(key, val, invbyval, fwdbykey):
                # (key, val) duplicates an existing item -> no-op.
                return
            # key and val each duplicate a different existing item.
            if on_dup_kv is RAISE:
                raise KeyAndValueDuplicationError(key, val)
            elif on_dup_kv is IGNORE:
                return
            # else on_dup_kv is OVERWRITE. Fall through to return on last line.
        elif isdupkey:
            if on_dup_key is RAISE:
                raise KeyDuplicationError(key)
            elif on_dup_key is IGNORE:
                return
            # else on_dup_key is OVERWRITE. Fall through to return on last line.
        elif isdupval:
            if on_dup_val is RAISE:
                raise ValueDuplicationError(val)
            elif on_dup_val is IGNORE:
                return
            # else on_dup_val is OVERWRITE. Fall through to return on last line.
        # else neither isdupkey nor isdupval.
        return isdupkey, isdupval, invbyval, fwdbykey

    @staticmethod
    def _isdupitem(key, val, oldkey, oldval):
        dup = oldkey == key
        assert dup == (oldval == val)
        return dup

    def _write_item(self, key, val, isdupkey, isdupval, oldkey, oldval):
        fwdm = self.fwdm
        invm = self.invm
        fwdm[key] = val
        invm[val] = key
        if isdupkey:
            del invm[oldval]
        if isdupval:
            del fwdm[oldkey]
        return key, val, isdupkey, isdupval, oldkey, oldval

    def _update(self, init, on_dup_key, on_dup_val, on_dup_kv, *args, **kw):
        if not args and not kw:
            return
        if on_dup_kv is None:
            on_dup_kv = on_dup_val
        empty = not self
        only_copy_from_bimap = empty and not kw and isinstance(args[0], BidirectionalMapping)
        if only_copy_from_bimap:  # no need to check for duplication
            write_item = self._write_item
            for (key, val) in iteritems(args[0]):
                write_item(key, val, False, False, _MISS, _MISS)
            return
        raise_on_dup = RAISE in (on_dup_key, on_dup_val, on_dup_kv)
        rollback = raise_on_dup and not init
        if rollback:
            return self._update_with_rollback(on_dup_key, on_dup_val, on_dup_kv, *args, **kw)
        _put = self._put
        for (key, val) in pairs(*args, **kw):
            _put(key, val, on_dup_key, on_dup_val, on_dup_kv)

    def _update_with_rollback(self, on_dup_key, on_dup_val, on_dup_kv, *args, **kw):
        """Update, rolling back on failure."""
        writes = []
        appendwrite = writes.append
        dedup_item = self._dedup_item
        write_item = self._write_item
        for (key, val) in pairs(*args, **kw):
            try:
                dedup_result = dedup_item(key, val, on_dup_key, on_dup_val, on_dup_kv)
            except DuplicationError:
                undo_write = self._undo_write
                for write in reversed(writes):
                    undo_write(*write)
                raise
            if dedup_result:
                write_result = write_item(key, val, *dedup_result)
                appendwrite(write_result)

    def _undo_write(self, key, val, isdupkey, isdupval, oldkey, oldval):
        if not isdupkey and not isdupval:
            self._pop(key)
            return
        fwdm = self.fwdm
        invm = self.invm
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
        # object.__new__ to create a copy instance while bypassing its __init__, which would result
        # in copying this bidict's items into the copy instance one at a time. Instead, make whole
        # copies of each of the backing mappings, and make them the backing mappings of the copy,
        # avoiding copying items one at a time.
        copy = object.__new__(self.__class__)
        copy.fwdm = self.fwdm.copy()
        copy.invm = self.invm.copy()
        copy._init_inv()  # pylint: disable=protected-access
        return copy

    __copy__ = copy

    def __len__(self):
        """The number of contained items."""
        return len(self.fwdm)

    def __iter__(self):
        """Iterator over the contained items."""
        return iter(self.fwdm)

    def __getitem__(self, key):
        """``x.__getitem__(key) <==> x[key]``"""
        return self.fwdm[key]

    def values(self):
        """A set-like object providing a view on the contained values.

        Note that because the values of a :class:`~bidict.BidirectionalMapping`
        are the keys of its inverse,
        this returns a :class:`~collections.abc.KeysView`
        rather than a :class:`~collections.abc.ValuesView`,
        which has the advantage of supporting set operations.
        """
        return self.inv.keys()

    if PY2:
        def viewkeys(self):
            """A set-like object providing a view on the contained keys."""
            return self.fwdm.viewkeys()

        def viewvalues(self):  # noqa: D102; pylint: disable=missing-docstring
            return self.inv.viewkeys()
        viewvalues.__doc__ = values.__doc__
        values.__doc__ = "A list of the contained values."

        def viewitems(self):
            """A set-like object providing a view on the contained items."""
            return ItemsView(self)

        # __ne__ added automatically in Python 3 when you implement __eq__, but not in Python 2.
        def __ne__(self, other):
            """``x.__ne__(other) <==> x != other``"""
            return not self == other  # Implement __ne__ in terms of __eq__.


#==============================================================================
#  ← Prev: _abc.py           * Code review nav *           Next: _bidict.py →
#==============================================================================

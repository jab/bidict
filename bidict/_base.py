# Copyright 2009-2022 Joshua Bronson. All Rights Reserved.
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


"""Provide :class:`BidictBase`."""

import typing as _t
import weakref
from copy import copy
from itertools import starmap
from operator import eq

from ._abc import BidirectionalMapping
from ._dup import ON_DUP_DEFAULT, RAISE, DROP_OLD, DROP_NEW, OnDup
from ._exc import DuplicationError, KeyDuplicationError, ValueDuplicationError, KeyAndValueDuplicationError
from ._iter import _iteritems_args_kw
from ._typing import KT, VT, NONEType, NONE, OKT, OVT, IterItems, MapOrIterItems, KeysView, ItemsView


# Alias for better readability in dedup results below:
NOOP = NONE
NOOPT = NONEType
OLDKV = _t.Tuple[OKT[KT], OVT[VT]]
DedupResult = _t.Union[OLDKV[KT, VT], NOOPT]
WriteResult = _t.Tuple[KT, VT, OKT[KT], OVT[VT]]
BT = _t.TypeVar('BT', bound='BidictBase[_t.Any, _t.Any]')


class BidictBase(BidirectionalMapping[KT, VT]):
    """Base class implementing :class:`BidirectionalMapping`."""

    #: The default :class:`~bidict.OnDup`
    #: that governs behavior when a provided item
    #: duplicates the key or value of other item(s).
    #:
    #: *See also* :ref:`basic-usage:Values Must Be Unique`, :doc:`extending`
    on_dup = ON_DUP_DEFAULT

    _fwdm: _t.MutableMapping[KT, VT]  #: the backing forward mapping (*key* → *val*)
    _invm: _t.MutableMapping[VT, KT]  #: the backing inverse mapping (*val* → *key*)
    _fwdm_cls: _t.Type[_t.MutableMapping[KT, VT]] = dict  #: class of the backing forward mapping
    _invm_cls: _t.Type[_t.MutableMapping[VT, KT]] = dict  #: class of the backing inverse mapping

    #: The inverse bidict instance. If None, then ``_invweak`` is not None.
    _inv: '_t.Optional[BidictBase[VT, KT]]'
    #: The class of the inverse bidict instance.
    _inv_cls: '_t.Type[BidictBase[VT, KT]]'
    #: A weak reference to the inverse bidict instance. If None, then ``_inv`` is not None.
    _invweak: '_t.Optional[weakref.ReferenceType[BidictBase[VT, KT]]]'

    #: The object used by :meth:`__repr__` for printing the contained items.
    _repr_delegate: _t.Any = dict

    def __init_subclass__(cls, **kw: _t.Any) -> None:
        super().__init_subclass__(**kw)
        # Compute and set _inv_cls, the inverse of this bidict class.
        # See https://bidict.readthedocs.io/extending.html#dynamic-inverse-class-generation
        # for an explanation of this along with motivating examples.
        if '_inv_cls' in cls.__dict__:  # Already computed and cached (see below).
            return
        if cls._fwdm_cls is cls._invm_cls:  # The bidict class is its own inverse.
            cls._inv_cls = cls
            return
        # Compute the inverse class, e.g. with _fwdm_cls and _invm_cls swapped.
        inv_cls = type(cls.__name__ + 'Inv', cls.__bases__, {
            **cls.__dict__,
            '_inv_cls': cls,
            '_fwdm_cls': cls._invm_cls,
            '_invm_cls': cls._fwdm_cls,
        })
        cls._inv_cls = inv_cls  # Cache for the future.

    @_t.overload
    def __init__(self: 'BidictBase[KT, VT]') -> None: ...
    @_t.overload
    def __init__(self: 'BidictBase[KT, VT]', __m: _t.Mapping[KT, VT]) -> None: ...
    @_t.overload
    def __init__(self: 'BidictBase[KT, VT]', __i: IterItems[KT, VT]) -> None: ...
    @_t.overload
    def __init__(self: 'BidictBase[str, VT]', **kw: VT) -> None: ...
    @_t.overload
    def __init__(self: 'BidictBase[str, VT]', __m: _t.Mapping[str, VT], **kw: VT) -> None: ...
    @_t.overload
    def __init__(self: 'BidictBase[str, VT]', __i: IterItems[str, VT], **kw: VT) -> None: ...
    def __init__(self, *args: MapOrIterItems[_t.Any, VT], **kw: VT) -> None:
        """Make a new bidirectional mapping.
        The signature behaves like that of :class:`dict`.
        Items passed in are added in the order they are passed,
        respecting the :attr:`on_dup` class attribute in the process.
        """
        self._fwdm = self._fwdm_cls()
        self._invm = self._invm_cls()
        self._init_inv()
        if args or kw:
            self._update(True, self.on_dup, *args, **kw)

    def _init_inv(self) -> None:
        # Create the inverse bidict instance via __new__, bypassing its __init__ so that its
        # _fwdm and _invm can be assigned to this bidict's _invm and _fwdm. Store it in self._inv,
        # which holds a strong reference to a bidict's inverse, if one is available.
        self._inv = inv = self._inv_cls.__new__(self._inv_cls)
        inv._fwdm = self._invm
        inv._invm = self._fwdm
        # Only give the inverse a weak reference to this bidict to avoid creating a reference cycle,
        # stored in the _invweak attribute. See also the docs in
        # :ref:`addendum:Bidict Avoids Reference Cycles`
        inv._inv = None
        inv._invweak = weakref.ref(self)
        # Since this bidict has a strong reference to its inverse already, set its _invweak to None.
        self._invweak = None

    @property
    def _isinv(self) -> bool:
        return self._inv is None

    @property
    def inverse(self) -> 'BidictBase[VT, KT]':
        """The inverse of this bidict."""
        # Resolve and return a strong reference to the inverse bidict.
        # One may be stored in self._inv already.
        if self._inv is not None:
            return self._inv
        # Otherwise a weakref is stored in self._invweak. Try to get a strong ref from it.
        assert self._invweak is not None
        inv = self._invweak()
        if inv is not None:
            return inv
        # Refcount of referent must have dropped to zero, as in `bidict().inv.inv`. Init a new one.
        self._init_inv()  # Now this bidict will retain a strong ref to its inverse.
        assert self._inv is not None
        return self._inv

    #: Alias for :attr:`inverse`.
    inv = inverse

    def __repr__(self) -> str:
        """See :func:`repr`."""
        clsname = self.__class__.__name__
        items = self._repr_delegate(self.items()) if self else ''
        return f'{clsname}({items})'

    # The inherited collections.abc.Mapping.keys() method returns a collections.abc.KeysView,
    # which is currently implemented in pure Python rather than optimized C, so override:
    def keys(self) -> KeysView[KT]:
        """A set-like object providing a view on the contained keys.

        Returns a dict_keys object that behaves exactly the same as collections.abc.KeysView(b),
        except for (1) being faster when running on CPython, (2) being reversible,
        and (3) having a .mapping attribute in Python 3.10+ that exposes a mappingproxy
        pointing back to the (one-way) forward dictionary that backs this bidict.
        """
        return self._fwdm.keys()  # type: ignore [return-value]

    # The inherited collections.abc.Mapping.values() method returns a collections.abc.ValuesView, so override:
    def values(self) -> KeysView[VT]:
        """A set-like object providing a view on the contained values.

        Since the values of a bidict are equivalent to the keys of its inverse,
        this method returns a KeysView for this bidict's inverse
        rather than just a ValuesView for this bidict.
        The KeysView offers the benefit of supporting set operations
        (including constant- rather than linear-time containment checks)
        and is just as cheap to provide as the less capable ValuesView would be.

        Returns a dict_keys object that behaves exactly the same as collections.abc.KeysView(b.inverse),
        except for (1) being faster when running on CPython, (2) being reversible,
        and (3) having a .mapping attribute in Python 3.10+ that exposes a mappingproxy
        pointing back to the (one-way) inverse dictionary that backs this bidict.
        """
        return self.inverse.keys()

    # The inherited collections.abc.Mapping.items() methods returns a collections.abc.ItemsView,
    # which is currently implemented in pure Python rather than optimized C, so override:
    def items(self) -> ItemsView[KT, VT]:
        """A set-like object providing a view on the contained items.

        Returns a dict_items object that behaves exactly the same as collections.abc.ItemsView(b),
        except for being much faster when running on CPython, being reversible,
        and having a .mapping attribute in Python 3.10+ that exposes a mappingproxy
        pointing back to the (one-way) forward dictionary that backs this bidict.
        """
        return self._fwdm.items()  # type: ignore [return-value]

    # The inherited collections.abc.Mapping.__contains__() method is implemented by doing a ``try``
    # ``except KeyError`` around ``self[key]``. The following implementation is much faster,
    # especially in the missing case.
    def __contains__(self, key: _t.Any) -> bool:
        """True if the mapping contains the specified key, else False."""
        return key in self._fwdm

    # The inherited collections.abc.Mapping.__eq__() method is implemented in terms of an inefficient
    # ``dict(self.items()) == dict(other.items())`` comparison, so override it with a
    # more efficient implementation.
    def __eq__(self, other: object) -> bool:
        """*x.__eq__(other)　⟺　x == other*

        Equivalent to *dict(x.items()) == dict(other.items())*
        but more efficient.

        Note that :meth:`bidict's __eq__() <bidict.bidict.__eq__>` implementation
        is inherited by subclasses,
        in particular by the ordered bidict subclasses,
        so even with ordered bidicts,
        :ref:`== comparison is order-insensitive <eq-order-insensitive>`.

        *See also* :meth:`equals_order_sensitive`
        """
        if isinstance(other, _t.Mapping):
            return self._fwdm.items() == other.items()
        return NotImplemented

    def equals_order_sensitive(self, other: object) -> bool:
        """Order-sensitive equality check.

        *See also* :ref:`eq-order-insensitive`
        """
        if not isinstance(other, _t.Mapping) or len(self) != len(other):
            return False
        return all(starmap(eq, zip(self.items(), other.items())))

    # The following methods are mutating and so are not public. But they are implemented in this
    # non-mutable base class (rather than the mutable `bidict` subclass) because they are used here
    # during initialization (starting with the `_update` method). (Why is this? Because `__init__`
    # and `update` share a lot of the same behavior (inserting the provided items while respecting
    # `on_dup`), so it makes sense for them to share implementation too.)
    def _pop(self, key: KT) -> VT:
        val = self._fwdm.pop(key)
        del self._invm[val]
        return val

    def _put(self, key: KT, val: VT, on_dup: OnDup) -> None:
        dedup_result = self._dedup(key, val, on_dup)
        if dedup_result is not NOOP:
            self._write(key, val, *dedup_result)

    def _dedup(self, key: KT, val: VT, on_dup: OnDup) -> DedupResult[KT, VT]:
        """Check *key* and *val* for any duplication in self.

        Handle any duplication as per the passed in *on_dup*.

        If (key, val) is already present, return :obj:`NOOP`
        since writing (key, val) would be a no-op.

        If duplication is found and the corresponding :class:`~bidict.OnDupAction` is
        :attr:`~bidict.DROP_NEW`, return :obj:`NOOP`.

        If duplication is found and the corresponding :class:`~bidict.OnDupAction` is
        :attr:`~bidict.RAISE`, raise the appropriate exception.

        If duplication is found and the corresponding :class:`~bidict.OnDupAction` is
        :attr:`~bidict.DROP_OLD`, or if no duplication is found,
        return *(oldkey, oldval)*.
        """
        fwdm, invm = self._fwdm, self._invm
        oldval: OVT[VT] = fwdm.get(key, NONE)
        oldkey: OKT[KT] = invm.get(val, NONE)
        isdupkey, isdupval = oldval is not NONE, oldkey is not NONE
        if isdupkey and isdupval:
            if key == oldkey:
                assert val == oldval
                # (key, val) duplicates an existing item -> no-op.
                return NOOP
            # key and val each duplicate a different existing item.
            if on_dup.kv is RAISE:
                raise KeyAndValueDuplicationError(key, val)
            if on_dup.kv is DROP_NEW:
                return NOOP
            assert on_dup.kv is DROP_OLD
            # Fall through to the return statement on the last line.
        elif isdupkey:
            if on_dup.key is RAISE:
                raise KeyDuplicationError(key)
            if on_dup.key is DROP_NEW:
                return NOOP
            assert on_dup.key is DROP_OLD
            # Fall through to the return statement on the last line.
        elif isdupval:
            if on_dup.val is RAISE:
                raise ValueDuplicationError(val)
            if on_dup.val is DROP_NEW:
                return NOOP
            assert on_dup.val is DROP_OLD
            # Fall through to the return statement on the last line.
        # else neither isdupkey nor isdupval.
        return (oldkey, oldval)

    def _write(self, newkey: KT, newval: VT, oldkey: OKT[KT], oldval: OVT[VT]) -> WriteResult[KT, VT]:
        self._fwdm[newkey] = newval
        self._invm[newval] = newkey
        if oldval is not NONE:
            del self._invm[oldval]
        if oldkey is not NONE:
            del self._fwdm[oldkey]
        return newkey, newval, oldkey, oldval

    def _undo_write(self, write_result: WriteResult[KT, VT]) -> None:
        newkey, newval, oldkey, oldval, *_ = write_result
        # mypy does not properly do type narrowing with the following, so inline below instead:
        # isdupkey, isdupval = oldval is not NONE, oldkey is not NONE
        if oldval is NONE and oldkey is NONE:  # not isdupkey and not isdupval
            self._pop(newkey)
            return
        if oldval is not NONE:  # isdupkey
            self._fwdm[newkey] = oldval
            self._invm[oldval] = newkey
            if oldkey is NONE:  # not isdupval
                del self._invm[newval]
        if oldkey is not NONE:  # isdupval
            self._invm[newval] = oldkey
            self._fwdm[oldkey] = newval
            if oldval is NONE:  # not isdupkey
                del self._fwdm[newkey]

    def _update(self, in_init: bool, on_dup: OnDup, *args: MapOrIterItems[KT, VT], **kw: VT) -> None:
        # args[0] may be a generator that yields many items, so process input in a single pass.
        if not args and not kw:
            return
        if not self and not kw and isinstance(args[0], BidirectionalMapping):
            self._update_no_dup_check(args[0])
            return
        if in_init or RAISE not in on_dup:
            self._update_no_rollback(on_dup, *args, **kw)
        else:
            self._update_with_rollback(on_dup, *args, **kw)

    def _update_no_dup_check(self, other: BidirectionalMapping[KT, VT]) -> None:
        write = self._write
        for (key, val) in other.items():
            write(key, val, NONE, NONE)

    def _update_no_rollback(self, on_dup: OnDup, *args: MapOrIterItems[KT, VT], **kw: VT) -> None:
        put = self._put
        for (key, val) in _iteritems_args_kw(*args, **kw):
            put(key, val, on_dup)

    def _update_with_rollback(self, on_dup: OnDup, *args: MapOrIterItems[KT, VT], **kw: VT) -> None:
        """Update, rolling back on failure."""
        writes: _t.List[WriteResult[KT, VT]] = []
        append, dedup, write, undo = writes.append, self._dedup, self._write, self._undo_write
        for (key, val) in _iteritems_args_kw(*args, **kw):
            try:
                dedup_result = dedup(key, val, on_dup)
            except DuplicationError:
                for w in reversed(writes):
                    undo(w)
                raise
            if dedup_result is not NOOP:
                write_result = write(key, val, *dedup_result)
                append(write_result)

    def copy(self: BT) -> BT:
        """Efficiently clone this bidict by (shallow) copying its internal structure."""
        # Could just ``return self.__class__(self)`` here, but the below is faster. The former
        # would copy this bidict's items into a new instance one at a time (checking for duplication
        # for each item), whereas the below makes copies of the backing mappings at once, at C speed,
        # and does not check for item duplication (since the backing mappings have been checked already).
        into = self.__class__()
        self._clone_into(into)
        return into

    def _clone_into(self: BT, other: BT) -> BT:
        """Efficiently clone this bidict by copying its internal structure into *other*."""
        other._fwdm = copy(self._fwdm)
        other._invm = copy(self._invm)
        other._init_inv()
        return other

    #: Used for the copy protocol.
    #: *See also* the :mod:`copy` module
    __copy__ = copy

    def __or__(self: BT, other: _t.Mapping[KT, VT]) -> BT:
        """Return self|other."""
        if not isinstance(other, _t.Mapping):
            return NotImplemented
        new = self.copy()
        new._update(False, self.on_dup, other)
        return new

    def __ror__(self: BT, other: _t.Mapping[KT, VT]) -> BT:
        """Return other|self."""
        if not isinstance(other, _t.Mapping):
            return NotImplemented
        new = self.__class__(other)
        new._update(False, self.on_dup, self)
        return new

    def __len__(self) -> int:
        """The number of contained items."""
        return len(self._fwdm)

    def __iter__(self) -> _t.Iterator[KT]:
        """Iterator over the contained keys."""
        return iter(self._fwdm)

    def __getitem__(self, key: KT) -> VT:
        """*x.__getitem__(key) ⟺ x[key]*"""
        return self._fwdm[key]

    def __reduce__(self: BT) -> _t.Tuple[_t.Type[BT], _t.Tuple[_t.Dict[KT, VT]]]:
        """Return state information for pickling (otherwise thwarted by _invweak weakref)."""
        return (type(self), (dict(self.items()),))

    # On Python 3.8+, dicts are reversible, so even non-Ordered bidicts can provide an efficient
    # __reversed__ implementation. (On Python < 3.8, they cannot.) Once support is dropped for
    # Python < 3.8, can remove the following if statement to provide __reversed__ unconditionally.
    if hasattr(_fwdm_cls, '__reversed__'):
        def __reversed__(self) -> _t.Iterator[KT]:
            """Iterator over the contained keys in reverse order."""
            return reversed(self._fwdm.keys())


#                             * Code review nav *
#==============================================================================
# ← Prev: _abc.py             Current: _base.py   Next:     _frozenbidict.py →
#==============================================================================

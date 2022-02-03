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

import typing as t
import weakref
from itertools import starmap
from operator import eq

from ._abc import BidirectionalMapping
from ._dup import ON_DUP_DEFAULT, RAISE, DROP_OLD, DROP_NEW, OnDup
from ._exc import DuplicationError, KeyDuplicationError, ValueDuplicationError, KeyAndValueDuplicationError
from ._iter import _iteritems_args_kw
from ._typing import KT, VT, MISSING, OKT, OVT, IterItems, MapOrIterItems


OLDKV = t.Tuple[OKT[KT], OVT[VT]]
DedupResult = t.Optional[OLDKV[KT, VT]]
PartialWrite = t.Sequence[t.Any]
Write = t.List[PartialWrite]
Unwrite = Write
PreparedWrite = t.Tuple[Write, Unwrite]
BT = t.TypeVar('BT', bound='BidictBase[t.Any, t.Any]')


class BiMappingView(t.Generic[KT, VT], t.MappingView):
    """Bidict-specific MappingView subclass."""

    _mapping: 'BidictBase[KT, VT]'


class BiItemsView(BiMappingView[KT, VT], t.ItemsView[KT, VT], t.Reversible[t.Tuple[KT, VT]]):
    """All ItemsViews that bidicts provide are Reversible."""


class BiKeysView(BiMappingView[KT, VT], t.KeysView[KT], t.Reversible[KT], t.ValuesView[t.Any]):
    """All KeysViews that bidicts provide are Reversible and are also ValuesViews.

    Since the keys of a bidict are the values of its inverse (and vice versa),
    calling .values() on a bidict returns the same result as calling .keys() on its inverse,
    specifically a KeysView[KT] object that is also a ValuesView[VT].
    """


class BidictBase(BidirectionalMapping[KT, VT]):
    """Base class implementing :class:`BidirectionalMapping`."""

    #: The default :class:`~bidict.OnDup`
    #: that governs behavior when a provided item
    #: duplicates the key or value of other item(s).
    #:
    #: *See also* :ref:`basic-usage:Values Must Be Unique`, :doc:`extending`
    on_dup = ON_DUP_DEFAULT

    _fwdm: t.MutableMapping[KT, VT]  #: the backing forward mapping (*key* → *val*)
    _invm: t.MutableMapping[VT, KT]  #: the backing inverse mapping (*val* → *key*)
    _fwdm_cls: t.Type[t.MutableMapping[KT, VT]] = dict  #: class of the backing forward mapping
    _invm_cls: t.Type[t.MutableMapping[VT, KT]] = dict  #: class of the backing inverse mapping

    #: The inverse bidict instance. If None, then ``_invweak`` is not None.
    _inv: 't.Optional[BidictBase[VT, KT]]'
    #: The class of the inverse bidict instance.
    _inv_cls: 't.Type[BidictBase[VT, KT]]'
    #: A weak reference to the inverse bidict instance. If None, then ``_inv`` is not None.
    _invweak: 't.Optional[weakref.ReferenceType[BidictBase[VT, KT]]]'

    #: The object used by :meth:`__repr__` for printing the contained items.
    _repr_delegate: t.Any = dict

    def __init_subclass__(cls, **kw: t.Any) -> None:
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

    @t.overload
    def __init__(self: 'BidictBase[KT, VT]') -> None: ...
    @t.overload
    def __init__(self: 'BidictBase[KT, VT]', __m: t.Mapping[KT, VT]) -> None: ...
    @t.overload
    def __init__(self: 'BidictBase[KT, VT]', __i: IterItems[KT, VT]) -> None: ...
    @t.overload
    def __init__(self: 'BidictBase[str, VT]', **kw: VT) -> None: ...
    @t.overload
    def __init__(self: 'BidictBase[str, VT]', __m: t.Mapping[str, VT], **kw: VT) -> None: ...
    @t.overload
    def __init__(self: 'BidictBase[str, VT]', __i: IterItems[str, VT], **kw: VT) -> None: ...
    def __init__(self, *args: MapOrIterItems[t.Any, VT], **kw: VT) -> None:
        """Make a new bidirectional mapping.
        The signature behaves like that of :class:`dict`.
        Items passed in are added in the order they are passed,
        respecting the :attr:`on_dup` class attribute in the process.
        """
        self._fwdm = self._fwdm_cls()
        self._invm = self._invm_cls()
        self._init_inv()
        if args or kw:
            self._update(args=args, kw=kw, rbof=False)

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
    # which is currently implemented in slow, pure Python rather than optimized C, so override:
    def keys(self) -> BiKeysView[KT, VT]:
        """A set-like object providing a view on the contained keys.

        Returns a dict_keys object that behaves exactly the same as collections.abc.KeysView(b),
        except for (1) being faster when running on CPython, (2) being reversible,
        and (3) having a .mapping attribute in Python 3.10+ that exposes a mappingproxy
        pointing back to the (one-way) forward dictionary that backs this bidict.
        """
        return self._fwdm.keys()  # type: ignore [return-value]

    # The inherited collections.abc.Mapping.values() method returns a collections.abc.ValuesView, so override:
    def values(self) -> BiKeysView[VT, KT]:
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

    # The inherited collections.abc.Mapping.items() method returns a collections.abc.ItemsView,
    # which is currently implemented in slow, pure Python rather than optimized C, so override:
    def items(self) -> BiItemsView[KT, VT]:
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
    def __contains__(self, key: t.Any) -> bool:
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
        if isinstance(other, t.Mapping):
            return self._fwdm.items() == other.items()
        # Ref: https://docs.python.org/3/library/constants.html#NotImplemented
        return NotImplemented

    def equals_order_sensitive(self, other: object) -> bool:
        """Order-sensitive equality check.

        *See also* :ref:`eq-order-insensitive`
        """
        if not isinstance(other, t.Mapping) or len(self) != len(other):
            return False
        return all(starmap(eq, zip(self.items(), other.items())))

    # The following methods are mutating and so are not public. But they are implemented in this
    # non-mutable base class (rather than the mutable `bidict` subclass) because they are used
    # during initialization. (`__init__` and `update` share a lot of the same behavior, so it makes
    # sense for them to share implementation too.)
    def _pop(self, key: KT) -> VT:
        val = self._fwdm.pop(key)
        del self._invm[val]
        return val

    def _dedup(self, key: KT, val: VT, on_dup: OnDup) -> DedupResult[KT, VT]:
        """Check *key* and *val* for any duplication in self.

        Handle any duplication as per the passed in *on_dup*.

        If (key, val) is already present, return None
        since writing (key, val) would be a no-op.

        If duplication is found and the corresponding :class:`~bidict.OnDupAction` is
        :attr:`~bidict.DROP_NEW`, return None.

        If duplication is found and the corresponding :class:`~bidict.OnDupAction` is
        :attr:`~bidict.RAISE`, raise the appropriate exception.

        If duplication is found and the corresponding :class:`~bidict.OnDupAction` is
        :attr:`~bidict.DROP_OLD`, or if no duplication is found,
        return *(oldkey, oldval)*.
        """
        fwdm, invm = self._fwdm, self._invm
        oldval: OVT[VT] = fwdm.get(key, MISSING)
        oldkey: OKT[KT] = invm.get(val, MISSING)
        isdupkey, isdupval = oldval is not MISSING, oldkey is not MISSING
        if isdupkey and isdupval:
            if key == oldkey:
                assert val == oldval
                # (key, val) duplicates an existing item -> no-op.
                return None
            # key and val each duplicate a different existing item.
            if on_dup.kv is RAISE:
                raise KeyAndValueDuplicationError(key, val)
            if on_dup.kv is DROP_NEW:
                return None
            assert on_dup.kv is DROP_OLD
            # Fall through to the return statement on the last line.
        elif isdupkey:
            if on_dup.key is RAISE:
                raise KeyDuplicationError(key)
            if on_dup.key is DROP_NEW:
                return None
            assert on_dup.key is DROP_OLD
            # Fall through to the return statement on the last line.
        elif isdupval:
            if on_dup.val is RAISE:
                raise ValueDuplicationError(val)
            if on_dup.val is DROP_NEW:
                return None
            assert on_dup.val is DROP_OLD
            # Fall through to the return statement on the last line.
        # else neither isdupkey nor isdupval.
        return (oldkey, oldval)

    def _prep_write(self, newkey: KT, newval: VT, oldkey: OKT[KT], oldval: OVT[VT], save_unwrite: bool) -> PreparedWrite:
        fwdm, invm = self._fwdm, self._invm
        write: Write = [
            (fwdm.__setitem__, newkey, newval),
            (invm.__setitem__, newval, newkey),
        ]
        unwrite: Unwrite
        if oldval is MISSING and oldkey is MISSING:  # no key or value duplication
            # {0: 1, 2: 3} + (4, 5) => {0: 1, 2: 3, 4: 5}
            unwrite = [
                (fwdm.__delitem__, newkey),
                (invm.__delitem__, newval),
            ] if save_unwrite else []
        elif oldval is not MISSING and oldkey is not MISSING:  # key and value duplication across two different items
            # {0: 1, 2: 3} + (0, 3) => {0: 3}
            write.extend((
                (fwdm.__delitem__, oldkey),
                (invm.__delitem__, oldval),
            ))
            unwrite = [
                (fwdm.__setitem__, newkey, oldval),
                (invm.__setitem__, oldval, newkey),
                (fwdm.__setitem__, oldkey, newval),
                (invm.__setitem__, newval, oldkey),
            ] if save_unwrite else []
        elif oldval is not MISSING:  # just key duplication
            # {0: 1, 2: 3} + (2, 4) => {0: 1, 2: 4}
            #        nk ov   nk  nv
            write.append((invm.__delitem__, oldval))
            unwrite = [
                (fwdm.__setitem__, newkey, oldval),
                (invm.__setitem__, oldval, newkey),
                (invm.__delitem__, newval),
            ] if save_unwrite else []
        else:
            assert oldkey is not MISSING  # just value duplication
            # {0: 1, 2: 3} + (4, 3) => {0: 1, 4: 3}
            write.append((fwdm.__delitem__, oldkey))
            unwrite = [
                (fwdm.__setitem__, oldkey, newval),
                (invm.__setitem__, newval, oldkey),
                (fwdm.__delitem__, newkey),
            ] if save_unwrite else []
        return write, unwrite

    def _update(
        self,
        args: t.Tuple[MapOrIterItems[KT, VT], ...] = (),
        kw: t.Optional[t.Mapping[str, VT]] = None,
        rbof: t.Optional[bool] = None,
        on_dup: t.Optional[OnDup] = None,
    ) -> None:
        """Update, possibly rolling back on failure as per *rbof*."""
        # Note: args[0] may be a generator that yields many items, so process input in a single pass.
        if not args and not kw:
            return
        args_len = len(args)
        if args_len > 1:
            raise TypeError(f'Expected at most 1 positional argument, got {args_len}')
        if on_dup is None:
            on_dup = self.on_dup
        if rbof is None:
            rbof = RAISE in on_dup
        if kw is None:
            kw = {}
        other = args[0] if args else ()
        if not self and not kw:
            if isinstance(other, BidictBase):  # can skip dup check
                self._init_from(other)
                return
            # If other is not a BidictBase, fall through to the general treatment below,
            # which includes duplication checking. (If other is some BidirectionalMapping
            # that does not inherit from BidictBase, it's a foreign implementation, so we
            # perform duplication checking to err on the safe side.)

        # If we roll back on failure and we know that there are more updates to process than
        # already-contained items, our rollback strategy is to update a copy of self (without
        # rolling back on failure), and then to become the copy if all updates succeed.
        if rbof and isinstance(other, t.Sized) and len(other) + len(kw) > len(self):
            target = self.copy()
            target._update(args=args, kw=kw, rbof=False, on_dup=on_dup)
            self._init_from(target)
            return

        # There are more already-contained items than updates to process, or we don't know
        # how many updates there are to process. If we need to roll back on failure,
        # save a log of Unwrites as we update so we can undo changes if the update fails.
        unwrites: t.List[Unwrite] = []
        append_unwrite = unwrites.append
        prep_write = self._prep_write
        for (key, val) in _iteritems_args_kw(*args, **kw):
            try:
                dedup_result = self._dedup(key, val, on_dup)
            except DuplicationError:
                if rbof:
                    while unwrites:  # apply saved unwrites
                        unwrite = unwrites.pop()
                        for op, *opargs in unwrite:
                            op(*opargs)
                raise
            if dedup_result is None:  # no-op
                continue
            write, unwrite = prep_write(key, val, *dedup_result, save_unwrite=rbof)
            for op, *opargs in write:  # apply the write
                op(*opargs)
            if rbof and unwrite:  # save the unwrite for later application if needed
                append_unwrite(unwrite)

    def copy(self: BT) -> BT:
        """Make a (shallow) copy of this bidict."""
        # Could just ``return self.__class__(self)`` here, but the below is faster. The former
        # would copy this bidict's items into a new instance one at a time (checking for duplication
        # for each item), whereas the below makes copies of the backing mappings at once, at C speed,
        # and does not check for item duplication (since the backing mappings have been checked already).
        into = self.__class__()
        into._init_from(self)
        return into

    def _init_from(self, other: 'BidictBase[KT, VT]') -> None:
        self._fwdm.clear()
        self._invm.clear()
        self._fwdm.update(other._fwdm)
        self._invm.update(other._invm)

    #: Used for the copy protocol.
    #: *See also* the :mod:`copy` module
    __copy__ = copy

    def __or__(self: BT, other: t.Mapping[KT, VT]) -> BT:
        """Return self|other."""
        if not isinstance(other, t.Mapping):
            return NotImplemented
        new = self.copy()
        new._update(args=(other,), rbof=False)
        return new

    def __ror__(self: BT, other: t.Mapping[KT, VT]) -> BT:
        """Return other|self."""
        if not isinstance(other, t.Mapping):
            return NotImplemented
        new = self.__class__(other)
        new._update(args=(self,), rbof=False)
        return new

    def __len__(self) -> int:
        """The number of contained items."""
        return len(self._fwdm)

    def __iter__(self) -> t.Iterator[KT]:
        """Iterator over the contained keys."""
        return iter(self._fwdm)

    def __getitem__(self, key: KT) -> VT:
        """*x.__getitem__(key) ⟺ x[key]*"""
        return self._fwdm[key]

    def __reduce__(self: BT) -> t.Tuple[t.Type[BT], t.Tuple[t.Dict[KT, VT]]]:
        """Return state information for pickling (otherwise thwarted by _invweak weakref)."""
        return (type(self), (dict(self.items()),))

    # On Python 3.8+, dicts are reversible, so even non-Ordered bidicts can provide an efficient
    # __reversed__ implementation. (On Python < 3.8, they cannot.) Once support is dropped for
    # Python < 3.8, can remove the following if statement to provide __reversed__ unconditionally.
    if hasattr(_fwdm_cls, '__reversed__'):
        def __reversed__(self) -> t.Iterator[KT]:
            """Iterator over the contained keys in reverse order."""
            return reversed(self._fwdm.keys())


#                             * Code review nav *
#==============================================================================
# ← Prev: _abc.py             Current: _base.py   Next:     _frozenbidict.py →
#==============================================================================

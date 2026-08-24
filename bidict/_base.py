# Copyright 2009-2026 Joshua Bronson. All rights reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


#                             * Code review nav *
#                        (see comments in __init__.py)
# ============================================================================
# ← Prev: _abc.py              Current: _base.py            Next: _frozen.py →
# ============================================================================


"""Provide :class:`BidictBase`."""

from __future__ import annotations

import typing as t
import weakref
from collections.abc import ItemsView
from collections.abc import Iterable
from collections.abc import Iterator
from collections.abc import KeysView
from collections.abc import Mapping
from collections.abc import MutableMapping
from collections.abc import Reversible
from collections.abc import Set
from collections.abc import Sized
from collections.abc import ValuesView
from operator import eq
from types import MappingProxyType

from ._abc import BidirectionalMapping
from ._dup import DROP_NEW
from ._dup import DROP_OLD
from ._dup import ON_DUP_DEFAULT
from ._dup import RAISE
from ._dup import OnDup
from ._exc import KeyAndValueDuplicationError
from ._exc import KeyDuplicationError
from ._exc import ValueDuplicationError
from ._iter import inverted
from ._iter import iteritems
from ._typing import KT
from ._typing import MISSING
from ._typing import OKT
from ._typing import OVT
from ._typing import VT
from ._typing import Maplike
from ._typing import MapOrItems
from ._typing import override


OldKV: t.TypeAlias = tuple[OKT[KT], OVT[VT]]
DedupResult: t.TypeAlias = OldKV[KT, VT] | None
Unwrites: t.TypeAlias = list[tuple[t.Any, ...]]
ReversedIter: t.TypeAlias = t.Callable[['BidictBase[KT, t.Any]'], Iterator[KT]]


class BidictKeysView(KeysView[KT], ValuesView[KT]):
    """Since the keys of a bidict are the values of its inverse (and vice versa),
    the :class:`~collections.abc.ValuesView` result of calling *bi.values()*
    is also a :class:`~collections.abc.KeysView` of *bi.inverse*.
    """


class ProxiedSetView:
    """Mixin for bidict views whose :class:`~collections.abc.Set` methods
    delegate to a backing dict view. See :func:`_override_set_methods_to_use_backing_dict`.

    *_viewname* names the view of *_mapping._fwdm* with the same elements as this view.
    """

    _mapping: BidictBase[t.Any, t.Any]
    _viewname: t.ClassVar[str]
    __slots__ = ()


class BidictValuesView(ProxiedSetView, BidictKeysView[VT]):
    """The set-like view returned by *bi.values()* for a non-ordered bidict.

    A bidict's values are the keys of its inverse, so the fast, set-like operations are
    all provided by viewing the inverse's keys, which this does by taking the *inverse*
    as its *_mapping*: the inherited __contains__ and __len__ then already do the right
    thing, and _mapping._fwdm is the backing mapping whose keys are our elements, so the
    set-method proxy below works unmodified.

    Iteration is the exception. The inverse's key order is its own backing mapping's,
    which diverges from this bidict's key order as soon as an item is overwritten. So
    iterate *this* bidict's backing mapping instead (i.e. the inverse's _invm), to keep
    b.values() corresponding elementwise to b.keys(), as it does for a plain dict.
    """

    _viewname: t.ClassVar[str] = 'keys'
    __slots__ = ()

    @override
    def __iter__(self) -> Iterator[VT]:
        return iter(self._mapping._invm.values())

    def __reversed__(self) -> Iterator[VT]:
        return reversed(t.cast('Reversible[VT]', self._mapping._invm.values()))


class _NonReversibleBidictValuesView(BidictValuesView[VT]):
    """The values view of a bidict whose backing mappings are not reversible.

    Setting __reversed__ to None keeps issubclass(cls, Reversible) false, the same way
    BidictBase._set_reversed() does for the bidict itself, so that this view does not
    advertise support for reversed() that the backing mappings cannot deliver.
    """

    __reversed__: t.ClassVar[None] = None  # type: ignore[assignment]
    __slots__ = ()


class BidictBase(BidirectionalMapping[KT, VT]):
    """Base class implementing :class:`BidirectionalMapping`."""

    #: The default :class:`~bidict.OnDup`
    #: that governs behavior when a provided item
    #: duplicates the key or value of other item(s).
    #:
    #: *See also*
    #: :ref:`basic-usage:Values Must Be Unique` (https://bidict.rtfd.io/basic-usage.html#values-must-be-unique),
    #: :doc:`extending` (https://bidict.rtfd.io/extending.html)
    on_dup = ON_DUP_DEFAULT

    _fwdm: MutableMapping[KT, VT]  #: the backing forward mapping (*key* → *val*)
    _invm: MutableMapping[VT, KT]  #: the backing inverse mapping (*val* → *key*)
    _fwdm_cls: t.ClassVar[type[MutableMapping[t.Any, t.Any]]] = dict  #: class of the backing forward mapping
    _invm_cls: t.ClassVar[type[MutableMapping[t.Any, t.Any]]] = dict  #: class of the backing inverse mapping
    _fwdm_is_dict: t.ClassVar[bool] = True

    # When a bidict's `.inverse` property is accessed for the first time, the inverse instance is computed on demand
    # and stored for subsequent use. A reference back to itself is also stored on the inverse instance at the same time.
    # A weakref is used in the inverse direction to avoid creating a reference cycle. See :meth:`inverse`
    _inv: BidictBase[VT, KT] | None
    _invweak: weakref.ReferenceType[BidictBase[VT, KT]] | None
    _inv_cls: t.ClassVar[type[BidictBase[t.Any, t.Any]]]  # the inverse bidict's class, see :meth:`_ensure_inv_cls`
    _values_view_cls: t.ClassVar[type[BidictValuesView[t.Any]]]  # see :meth:`_set_reversed`

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()
        cls._init_class()

    @classmethod
    def _init_class(cls) -> None:
        cls._fwdm_is_dict = issubclass(cls._fwdm_cls, dict)
        cls._ensure_inv_cls()
        cls._set_reversed()

    __reversed__: t.ClassVar[ReversedIter[t.Any] | None]
    #: Whether __reversed__ was provided by a user rather than by :meth:`_set_reversed`.
    #: Inherited, so that a subclass of e.g. :class:`~bidict.OrderedBidictBase` keeps
    #: the implementation it inherits rather than computing one of its own.
    _reversed_is_user_provided: t.ClassVar[bool] = False

    @classmethod
    def _set_reversed(cls) -> None:
        """Set __reversed__ for subclasses that do not set it explicitly
        according to whether backing mappings are reversible.
        """
        backing_reversible = all(issubclass(i, Reversible) for i in (cls._fwdm_cls, cls._invm_cls))
        # Leave a user-provided __reversed__ alone, whether it is defined in this class's own
        # body (e.g. OrderedBidictBase's) or inherited from a base class that defined one
        # (e.g. OrderedBidict's). Crucially, a value *this* method assigned must not count as
        # user-provided: a subclass of a bidict whose backing mappings were not reversible
        # inherits the None assigned below, and must stay free to compute its own answer from
        # its own backing types, which may well be reversible.
        resolved = getattr(cls, '__reversed__', None)
        # Note Mapping.__reversed__ is None, which is what resolves here for BidictBase itself.
        user_impl = resolved is not None and resolved is not _fwdm_reversed
        # A user's explicit `__reversed__ = None` opt-out is indistinguishable by value from
        # the None assigned below, so look for it in the class's own namespace instead. Match
        # only that exact value: a bare membership test would also match a value assigned by a
        # previous call of this method, which would then be inherited as if a user had provided it.
        opted_out = getattr(cls, '__dict__', {}).get('__reversed__', MISSING) is None
        if user_impl or opted_out:
            cls._reversed_is_user_provided = True
        if not cls._reversed_is_user_provided:
            cls.__reversed__ = _fwdm_reversed if backing_reversible else None
        # values() iterates a backing mapping (see :meth:`values`), so its view can only
        # support reversed() if that mapping does, and should not offer it if this bidict
        # declines to offer reversed() itself.
        values_reversible = backing_reversible and cls.__reversed__ is not None
        cls._values_view_cls = BidictValuesView if values_reversible else _NonReversibleBidictValuesView

    @classmethod
    def _ensure_inv_cls(cls) -> None:
        """Ensure :attr:`_inv_cls` is set, computing it dynamically if necessary.

        All subclasses provided in :mod:`bidict` are their own inverse classes,
        i.e., their backing forward and inverse mappings are both the same type,
        but users may define subclasses where this is not the case.
        This method ensures that the inverse class is computed correctly regardless.

        See: :ref:`extending:Dynamic Inverse Class Generation`
        (https://bidict.rtfd.io/extending.html#dynamic-inverse-class-generation)
        """
        # This _ensure_inv_cls() method is (indirectly) corecursive with _make_inv_cls() below
        # in the case that we need to dynamically generate the inverse class:
        #   1. _ensure_inv_cls() calls cls._make_inv_cls()
        #   2. cls._make_inv_cls() calls type(..., (cls, ...), ...) to dynamically generate inv_cls
        #   3. Our __init_subclass__ hook (see above) is automatically called on inv_cls
        #   4. inv_cls.__init_subclass__() calls inv_cls._ensure_inv_cls()
        #   5. inv_cls._ensure_inv_cls() resolves to this implementation
        #      (inv_cls deliberately does not override this), so we're back where we started.
        # But since the _make_inv_cls() call will have set inv_cls.__dict__._inv_cls,
        # just check if it's already set before calling _make_inv_cls() to prevent infinite recursion.
        if getattr(cls, '__dict__', {}).get('_inv_cls'):  # Don't assume cls.__dict__
            return
        cls._inv_cls = cls._make_inv_cls()

    @classmethod
    def _make_inv_cls(cls) -> type[t.Self]:
        diff = cls._inv_cls_dict_diff()
        cls_is_own_inv = all(getattr(cls, k, MISSING) == v for (k, v) in diff.items())
        if cls_is_own_inv:
            return cls
        # Suppress auto-calculation of _inv_cls's _inv_cls since we know it already.
        # Works with the guard in BidictBase._ensure_inv_cls() to prevent infinite recursion.
        diff['_inv_cls'] = cls
        inv_cls = type(f'{cls.__name__}Inv', (cls, GeneratedBidictInverse), diff)
        inv_cls.__module__ = cls.__module__
        # Point __qualname__ at where this class actually lives, namely cls's _inv_cls attribute,
        # so that pickle can find it by reference like any other class. Without this it could not
        # be pickled at all, since nothing else refers to it by name. __name__ is left alone, so
        # repr() is unaffected.
        inv_cls.__qualname__ = f'{cls.__qualname__}._inv_cls'
        return t.cast('type[t.Self]', inv_cls)

    @classmethod
    def _inv_cls_dict_diff(cls) -> dict[str, t.Any]:
        return {
            '_fwdm_cls': cls._invm_cls,
            '_invm_cls': cls._fwdm_cls,
        }

    def __init__(self, arg: MapOrItems[KT, VT] = (), /, **kw: VT) -> None:
        """Make a new bidirectional mapping.
        The signature behaves like that of :class:`dict`.
        ktems passed via positional arg are processed first,
        followed by any items passed via keyword argument.
        Any duplication encountered along the way
        is handled as per :attr:`on_dup`.
        """
        self._fwdm = self._fwdm_cls()
        self._invm = self._invm_cls()
        self._update(arg, kw, rollback=False)

    @property
    @override
    def inverse(self) -> BidictBase[VT, KT]:
        """The inverse of this bidirectional mapping instance."""
        # First check if a strong reference is already stored.
        inv: BidictBase[VT, KT] | None = getattr(self, '_inv', None)
        if inv is not None:
            return inv
        # Next check if a weak reference is already stored.
        invweak = getattr(self, '_invweak', None)
        if invweak is not None:
            inv = invweak()  # Try to resolve a strong reference and return it.
            if inv is not None:
                return inv
        # No luck. Compute the inverse reference and store it for subsequent use.
        inv = self._make_inverse()
        self._inv = inv
        self._invweak = None
        # Also store a weak reference back to `instance` on its inverse instance, so that
        # the second `.inverse` access in `bi.inverse.inverse` hits the cached weakref.
        inv._inv = None
        inv._invweak = weakref.ref(self)
        # In e.g. `bidict().inverse.inverse`, this design ensures that a strong reference
        # back to the original instance is retained before its refcount drops to zero,
        # avoiding an unintended potential deallocation.
        return inv

    def _make_inverse(self) -> BidictBase[VT, KT]:
        inv: BidictBase[VT, KT] = self._inv_cls()
        inv._fwdm = self._invm
        inv._invm = self._fwdm
        return inv

    @property
    def inv(self) -> BidictBase[VT, KT]:
        """Alias for :attr:`inverse`."""
        return self.inverse

    @override
    def __repr__(self) -> str:
        """See :func:`repr`."""
        clsname = self.__class__.__name__
        items = dict(self.items()) if self else ''
        return f'{clsname}({items})'

    @override
    def values(self) -> BidictKeysView[VT]:
        """A set-like object providing a view on the contained values.

        Since the values of a bidict are equivalent to the keys of its inverse,
        this method returns a set-like object for this bidict's values
        rather than just a collections.abc.ValuesView.
        This object supports set operations like union and difference,
        and constant- rather than linear-time containment checks,
        and is no more expensive to provide than the less capable
        collections.abc.ValuesView would be.

        Like :class:`dict`, and unlike the inverse's :meth:`keys` view,
        it also yields this bidict's values in the same order as its keys,
        so that *zip(b.keys(), b.values())* corresponds elementwise to *b.items()*.

        See :meth:`keys` for more information.
        """
        return self._values_view_cls(self.inverse)

    @override
    def keys(self) -> KeysView[KT]:
        """A set-like object providing a view on the contained keys.

        When *b._fwdm* is a :class:`dict`, *b.keys()* returns its *dict_keys*,
        which behaves exactly the same as *collections.abc.KeysView(b)*, except for

          - offering better performance

          - being reversible

          - having a .mapping attribute in Python 3.10+
            that exposes a mappingproxy to *b._fwdm*.

        A :class:`dict` subclass gets the same treatment, via whatever view its own
        *keys()* returns. Only a backing mapping that is not a :class:`dict` at all
        falls back to a generic view over this bidict.
        """
        return self._fwdm.keys() if self._fwdm_is_dict else BidictKeysView(self)

    @override
    def items(self) -> ItemsView[KT, VT]:
        """A set-like object providing a view on the contained items.

        When *b._fwdm* is a :class:`dict`, *b.items()* returns its *dict_items*,
        which behaves exactly the same as *collections.abc.ItemsView(b)*, except for:

          - offering better performance

          - being reversible

          - having a .mapping attribute in Python 3.10+
            that exposes a mappingproxy to *b._fwdm*.

        See :meth:`keys` for how backing mappings that are not exactly dicts are handled.
        """
        return self._fwdm.items() if self._fwdm_is_dict else super().items()

    # The inherited collections.abc.Mapping.__contains__() method is implemented by doing a `try`
    # `except KeyError` around `self[key]`. The following implementation is much faster,
    # especially in the missing case.
    @override
    def __contains__(self, key: t.Any) -> bool:
        """True if the mapping contains the specified key, else False."""
        return key in self._fwdm

    # The inherited collections.abc.Mapping.__eq__() method is implemented in terms of an inefficient
    # `dict(self.items()) == dict(other.items())` comparison, so override it with a
    # more efficient implementation.
    @override
    def __eq__(self, other: object) -> bool:
        """*x.__eq__(other)　⟺　x == other*

        Equivalent to *dict(x.items()) == dict(other.items())*
        but more efficient.

        Note that :meth:`bidict's __eq__() <bidict.BidictBase.__eq__>` implementation
        is inherited by subclasses,
        in particular by the ordered bidict subclasses,
        so even with ordered bidicts,
        :ref:`== comparison is order-insensitive <eq-order-insensitive>`
        (https://bidict.rtfd.io/other-bidict-types.html#eq-is-order-insensitive).

        *See also* :meth:`equals_order_sensitive`
        """
        if isinstance(other, Mapping):
            return self._fwdm.items() == other.items()
        # Ref: https://docs.python.org/3/library/constants.html#NotImplemented
        return NotImplemented

    def equals_order_sensitive(self, other: object) -> bool:
        """Order-sensitive equality check.

        *See also* :ref:`eq-order-insensitive`
        (https://bidict.rtfd.io/other-bidict-types.html#eq-is-order-insensitive)
        """
        if not isinstance(other, Mapping) or len(self) != len(other):
            return False
        return all(map(eq, self.items(), other.items()))

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
        isdupkey = oldval is not MISSING
        isdupval = oldkey is not MISSING
        if isdupkey and isdupval:
            if fwdm[oldkey] is oldval:
                return None  # (key, val) duplicates an existing item -> no-op
            # key and val each duplicate a different existing item.
            if on_dup.val is RAISE:
                raise KeyAndValueDuplicationError(key, val)
            if on_dup.val is DROP_NEW:
                return None
            assert on_dup.val is DROP_OLD
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
        # else no key or value duplication.
        return oldkey, oldval

    def _write(self, newkey: KT, newval: VT, oldkey: OKT[KT], oldval: OVT[VT], unwrites: Unwrites | None) -> None:
        """Insert (newkey, newval), extending *unwrites* with associated inverse operations if provided.

        *oldkey* and *oldval* are as returned by :meth:`_dedup`.

        If *unwrites* is not None, it is extended with the inverse operations necessary to undo the write.
        This design allows :meth:`_update` to roll back a partially applied update that fails part-way through
        when necessary.

        This design also allows subclasses that require additional operations to easily extend this implementation.
        For example, :class:`bidict.OrderedBidictBase` calls this inherited implementation, and then extends *unwrites*
        with additional operations needed to keep its internal linked list nodes consistent with its items' order
        as changes are made.
        """
        fwdm, invm = self._fwdm, self._invm
        fwdm_set, invm_set = fwdm.__setitem__, invm.__setitem__
        fwdm_del, invm_del = fwdm.__delitem__, invm.__delitem__
        # When newkey or newval duplicates one already contained, adopt the object already
        # contained rather than the one passed in. Otherwise the two backing mappings would end
        # up referring to equal but distinct objects for the same item, since a dict keeps the
        # key object it already has when a key is overwritten but takes the new value object.
        # invm[oldval] is the contained key equal to newkey; fwdm[oldkey] the contained value
        # equal to newval. This also matches what a plain dict does on overwrite.
        if oldval is not MISSING:  # newkey duplicates a contained key
            newkey = invm[oldval]
        if oldkey is not MISSING:  # newval duplicates a contained value
            newval = fwdm[oldkey]
        # Record each unwrite as soon as its write succeeds, rather than all of them at the end:
        # a backing mapping is user-supplied (see _fwdm_cls/_invm_cls) and may reject a write, and
        # if it does, everything written before it still has to be undone. Note that the four
        # writes below touch four distinct slots, so the order they are undone in does not matter.
        fwdm_set(newkey, newval)
        if unwrites is not None:
            # {0: 1} | {2: 3} => del fwdm[2];  {0: 1} | {0: 3} => fwdm[0] = 1
            unwrites.append((fwdm_del, newkey) if oldval is MISSING else (fwdm_set, newkey, oldval))
        invm_set(newval, newkey)
        if unwrites is not None:
            # {0: 1} | {2: 3} => del invm[3];  {0: 1} | {2: 1} => invm[1] = 0
            unwrites.append((invm_del, newval) if oldkey is MISSING else (invm_set, newval, oldkey))
        if oldkey is not MISSING:  # newval duplicates the value of the item keyed by oldkey
            # {0: 1, 2: 3} | {4: 3} => {0: 1, 4: 3}
            fwdm_del(oldkey)
            if unwrites is not None:
                unwrites.append((fwdm_set, oldkey, newval))
        if oldval is not MISSING:  # newkey duplicates the key of the item valued by oldval
            # {0: 1, 2: 3} | {2: 4} => {0: 1, 2: 4}
            invm_del(oldval)
            if unwrites is not None:
                unwrites.append((invm_set, oldval, newkey))

    def _update(
        self,
        arg: MapOrItems[KT, VT],
        kw: Mapping[str, VT] = MappingProxyType({}),
        *,
        rollback: bool = True,
        on_dup: OnDup | None = None,
    ) -> None:
        """Update with the items from *arg* and *kw*, failing clean as per *rollback*.

        When *rollback* is true (the default), a failure part-way through leaves self
        exactly as it was before the update was attempted.

        Callers pass rollback=False only when self is a throwaway instance that is
        discarded if the update fails, and so has nothing to roll back to.
        """
        # Note: We must process input in a single pass, since arg may be a generator.
        if not isinstance(arg, (Iterable, Maplike)):
            raise TypeError(f"'{arg.__class__.__name__}' object is not iterable")
        if not arg and not kw:
            return
        if on_dup is None:
            on_dup = self.on_dup

        # Fast path when we're empty and updating only from another bidict (i.e. no dup vals in new items).
        if not self and not kw and isinstance(arg, BidictBase):
            self._init_from(arg)
            return

        # Fast path when we're adding more items than we contain already and rollback is enabled:
        # Update a copy of self with rollback disabled. Fail if that fails, otherwise become the copy.
        if rollback and isinstance(arg, Sized) and len(arg) + len(kw) > len(self):
            tmp = self.copy()
            tmp._update(arg, kw, rollback=False, on_dup=on_dup)
            self._init_from(tmp)
            return

        # In all other cases, benchmarking has indicated that the update is best implemented as follows:
        # For each new item, perform a dup check (raising if necessary), and apply the associated writes we need to
        # perform on our backing _fwdm and _invm mappings. If rollback is enabled, also compute the associated unwrites
        # as we go. If item unpacking, duplication checking, or writing raises while rollback is enabled, apply the
        # accumulated unwrites before re-raising, to ensure that we fail clean.
        write = self._write
        unwrites: Unwrites | None = [] if rollback else None
        try:
            for key, val in iteritems(arg, **kw):
                dedup_result = self._dedup(key, val, on_dup)
                if dedup_result is not None:
                    write(key, val, *dedup_result, unwrites=unwrites)
        except Exception:
            if unwrites is not None:
                for fn, *args in reversed(unwrites):
                    fn(*args)
            raise

    def __copy__(self) -> t.Self:
        """Used for the copy protocol. See the :mod:`copy` module."""
        return self.copy()

    def copy(self) -> t.Self:
        """Make a (shallow) copy of this bidict."""
        # Could just `return self.__class__(self)` here, but the below is faster. The former
        # would copy this bidict's items into a new instance one at a time (checking for duplication
        # for each item), whereas the below copies from the backing mappings all at once, and foregoes
        # item-by-item duplication checking since the backing mappings have been checked already.
        return self._from_other(self)

    @classmethod
    def _from_other(cls, other: MapOrItems[KT, VT]) -> t.Self:
        """Fast, private constructor based on :meth:`_init_from`."""
        inst = cls()
        inst._init_from(other)
        return inst

    def _init_from(self, other: MapOrItems[KT, VT]) -> None:
        """Fast init from *other*, bypassing item-by-item duplication checking."""
        self._fwdm.clear()
        self._invm.clear()
        self._fwdm.update(other)
        # If other is a bidict, use its existing backing inverse mapping, otherwise
        # other could be a generator that's now exhausted, so invert self._fwdm on the fly.
        if isinstance(other, BidictBase):
            self._invm.update(t.cast('BidictBase[KT, VT]', other).inverse)
        else:
            self._invm.update(inverted(self._fwdm))

    # other's type is Mapping rather than Maplike since bidict() | SupportsKeysAndGetItem({})
    # raises a TypeError, just like dict() | SupportsKeysAndGetItem({}) does.
    def __or__(self, other: Mapping[KT, VT]) -> t.Self:
        """Return self|other."""
        if not isinstance(other, Mapping):
            return NotImplemented
        new = self.copy()
        new._update(other, rollback=False)
        return new

    def __ror__(self, other: Mapping[KT, VT]) -> t.Self:
        """Return other|self."""
        if not isinstance(other, Mapping):
            return NotImplemented
        # False positive in ty: https://github.com/astral-sh/ty/issues/4278
        new = self.__class__(other)  # ty: ignore[invalid-argument-type]
        new._update(self, rollback=False)
        return new

    @override
    def __len__(self) -> int:
        """The number of contained items."""
        return len(self._fwdm)

    @override
    def __iter__(self) -> Iterator[KT]:
        """Iterator over the contained keys."""
        return iter(self._fwdm)

    @override
    def __getitem__(self, key: KT) -> VT:
        """*x.__getitem__(key) ⟺ x[key]*"""
        return self._fwdm[key]

    @override
    def __reduce__(self) -> tuple[t.Any, ...]:
        """Return state information for pickling."""
        return self.__class__._from_other, (dict(self),)


# See BidictBase._set_reversed() above.
def _fwdm_reversed(self: BidictBase[KT, t.Any]) -> Iterator[KT]:
    """Iterator over the contained keys in reverse order."""
    return reversed(t.cast('Reversible[KT]', self._fwdm))


BidictBase._init_class()


# For better performance, make ProxiedSetView subclasses delegate to backing dicts for the
# methods they inherit from collections.abc.Set. (Cannot delegate for __iter__ and
# __reversed__ since they are order-sensitive.) See also: https://bugs.python.org/issue46713
_setmethodnames: Iterable[str] = (
    '__lt__', '__le__', '__gt__', '__ge__', '__eq__', '__ne__', '__sub__', '__rsub__',
    '__or__', '__ror__', '__xor__', '__rxor__', '__and__', '__rand__', 'isdisjoint',
)  # fmt: skip


def _override_set_methods_to_use_backing_dict(cls: type[ProxiedSetView]) -> None:
    def make_proxy_method(methodname: str) -> t.Any:
        def method(self: ProxiedSetView, *args: t.Any) -> t.Any:
            fwdm = self._mapping._fwdm
            if not isinstance(fwdm, dict):  # dict view speedup not available, fall back to Set's implementation.
                return getattr(Set, methodname)(self, *args)
            fwdm_dict_view = getattr(fwdm, self._viewname)()
            fwdm_dict_view_method = getattr(fwdm_dict_view, methodname)
            # When the (single) arg is another ProxiedSetView backed by a dict, forward its
            # backing dict_keys/dict_items to the C-level method rather than the arg itself. C-level dict views
            # only interoperate with other C-level dict views, not with arbitrary Set subclasses, so e.g.
            # `dict_keys(ob1).__lt__(ob2.keys())` returns NotImplemented. With both sides returning
            # NotImplemented, Python either raises TypeError (for `<`, `<=`, `>`, `>=`) or falls back to the
            # wrong answer (e.g. identity-based `==`). Note arg's view may differ from self's (keys vs items),
            # so use arg._viewname; this also subsumes the same-type case, where it equals self._viewname.
            if len(args) == 1 and isinstance((arg := args[0]), ProxiedSetView) and isinstance(arg._mapping._fwdm, dict):
                arg_dict_view = getattr(arg._mapping._fwdm, arg._viewname)()
                return fwdm_dict_view_method(arg_dict_view)
            return fwdm_dict_view_method(*args)

        method.__name__ = methodname
        method.__qualname__ = f'{cls.__qualname__}.{methodname}'
        return method

    for name in _setmethodnames:
        setattr(cls, name, make_proxy_method(name))


_override_set_methods_to_use_backing_dict(BidictValuesView)


class GeneratedBidictInverse:
    """Base class for dynamically-generated inverse bidict classes."""


#                             * Code review nav *
# ============================================================================
# ← Prev: _abc.py              Current: _base.py            Next: _frozen.py →
# ============================================================================

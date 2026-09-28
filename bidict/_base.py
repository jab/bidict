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
from collections import OrderedDict
from collections.abc import ItemsView
from collections.abc import Iterable
from collections.abc import Iterator
from collections.abc import KeysView
from collections.abc import Mapping
from collections.abc import MutableMapping
from collections.abc import Reversible
from collections.abc import Set
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
from ._typing import MapOrItems
from ._typing import override


OldKV: t.TypeAlias = tuple[OKT[KT], OVT[VT]]
DedupResult: t.TypeAlias = OldKV[KT, VT] | None
Unwrites: t.TypeAlias = list[tuple[t.Any, ...]]
ReversedIter: t.TypeAlias = t.Callable[['BidictBase[KT, t.Any]'], Iterator[KT]]

# keys() and items() methods known to return dict views, i.e. dict_keys and dict_items (or subclasses of them).
_DICT_VIEW_METHODS: t.Final = ((dict.keys, dict.items), (OrderedDict.keys, OrderedDict.items))


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

    # Go straight to the backing mapping, rather than through _mapping.__len__ as MappingView's does.
    def __len__(self) -> int:
        return len(self._mapping._fwdm)


class BidictValuesView(ProxiedSetView, BidictKeysView[VT]):
    """The set-like view returned by *bi.values()* for a non-ordered bidict.

    A bidict's values are the keys of its inverse, so the fast, set-like operations are
    all provided by viewing the inverse's keys, which this does by taking the *inverse*
    as its *_mapping*: _mapping._fwdm is then the backing mapping whose keys are our
    elements, so membership and len() can check it directly, and the set-method proxy
    below works unmodified.

    Iteration is the exception. The inverse's key order is its own backing mapping's,
    which diverges from this bidict's key order as soon as an item is overwritten. So
    iterate *this* bidict's backing mapping instead (i.e. the inverse's _invm), to keep
    b.values() corresponding elementwise to b.keys(), as it does for a plain dict.
    """

    _viewname: t.ClassVar[str] = 'keys'
    __slots__ = ()

    @override
    def __contains__(self, key: object) -> bool:
        return key in self._mapping._fwdm

    @override
    def __repr__(self) -> str:
        # Show the bidict whose values these are, as ValuesView(b) shows b, not the inverse in
        # _mapping, which would present our values as keys, and in its own order rather than ours.
        return f'{self.__class__.__name__}({self._mapping.inverse!r})'

    @override
    def __iter__(self) -> Iterator[VT]:
        return iter(self._mapping._invm.values())

    def __reversed__(self) -> Iterator[VT]:
        mapping = self._mapping._invm
        if isinstance(mapping, dict):
            return reversed(mapping.values())
        values = mapping.values()
        if isinstance(values, Reversible):
            return reversed(values)
        # A custom backing mapping's values view need not be reversible even when this bidict is,
        # so look the values up in the order that reversing this bidict gives its keys.
        bi: t.Any = self._mapping.inverse  # reversible, since this view is only used for bidicts that are
        return (mapping[key] for key in reversed(bi))


class _NonReversibleBidictValuesView(BidictValuesView[VT]):
    """The values view of a bidict that is not reversible.

    Setting __reversed__ to None keeps issubclass(cls, Reversible) false, the same way
    BidictBase._set_reversed() does for the bidict itself, so that this view does not
    advertise support for reversed() that the bidict declines to offer.
    """

    __reversed__: t.ClassVar[None] = None
    __slots__ = ()


# The keys() and items() views of an ordered bidict, and of a bidict whose backing forward mapping doesn't have
# dict views (see BidictBase.keys()), which gets the non-reversible variants below if it isn't reversible itself.
# They iterate the owning bidict, creating its iterator eagerly rather than inside the collections.abc
# generator methods, so that a mutation before the first next() call is detected too. Unlike those
# collections.abc views, they are reversible, by reversing the owning bidict.
class _KeysView(ProxiedSetView, BidictKeysView[KT]):
    _mapping: BidictBase[KT, t.Any]
    _viewname: t.ClassVar[str] = 'keys'
    __slots__ = ()

    # Membership does not depend on order, so check the backing mapping directly.
    @override
    def __contains__(self, key: object) -> bool:
        return key in self._mapping._fwdm

    @override
    def __iter__(self) -> Iterator[KT]:
        return iter(self._mapping)

    def __reversed__(self) -> Iterator[KT]:
        bi: t.Any = self._mapping  # reversible, since this view is only used for bidicts that are
        return reversed(bi)


class _ItemsView(ProxiedSetView, ItemsView[KT, VT]):
    _mapping: BidictBase[KT, VT]
    _viewname: t.ClassVar[str] = 'items'
    __slots__ = ()

    # Like a dict's views, these look values up in the backing mapping directly, not through the bidict.
    @override
    def __iter__(self) -> Iterator[tuple[KT, VT]]:
        bi = self._mapping
        fwdm = bi._fwdm
        return ((key, fwdm[key]) for key in bi)

    def __reversed__(self) -> Iterator[tuple[KT, VT]]:
        bi: t.Any = self._mapping  # reversible, since this view is only used for bidicts that are
        fwdm = bi._fwdm
        return ((key, fwdm[key]) for key in reversed(bi))

    @override
    def __contains__(self, item: tuple[t.Any, t.Any]) -> bool:
        # Like the Set methods proxied below, defer to the backing dict_items when there is one. (It can't
        # join them: their fallback, Set's own method, would be the abstract Container.__contains__.)
        bi = self._mapping
        fwdm = bi._fwdm
        if bi._fwdm_has_dict_views:
            return item in fwdm.items()
        # Otherwise do what dict_items does, where the inherited ItemsView.__contains__ would unpack item,
        # and so raise for anything but a pair, and match e.g. [key, value] too.
        if not isinstance(item, tuple) or len(item) != 2:
            return False
        key, value = item
        try:
            val = fwdm[key]
        except KeyError:
            return False
        return val is value or val == value


# The views of a bidict that is not reversible. See _NonReversibleBidictValuesView.
class _NonReversibleKeysView(_KeysView[KT]):
    __reversed__: t.ClassVar[None] = None
    __slots__ = ()


class _NonReversibleItemsView(_ItemsView[KT, VT]):
    __reversed__: t.ClassVar[None] = None
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
    _fwdm_has_dict_views: t.ClassVar[bool] = True  # see :meth:`_init_class`

    # When a bidict's `.inverse` property is accessed for the first time, the inverse instance is computed on demand
    # and stored for subsequent use. A reference back to itself is also stored on the inverse instance at the same time.
    # A weakref is used in the inverse direction to avoid creating a reference cycle. See :meth:`inverse`
    _inv: BidictBase[VT, KT] | None
    _invweak: weakref.ReferenceType[BidictBase[VT, KT]] | None
    _inv_cls: t.ClassVar[type[BidictBase[t.Any, t.Any]]]  # the inverse bidict's class, see :meth:`_ensure_inv_cls`
    _reversible: t.ClassVar[bool]  # whether this class offers reversed(), see :meth:`_set_reversed`

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()
        cls._init_class()

    @classmethod
    def _init_class(cls) -> None:
        # Not issubclass(fwdm_cls, dict): a dict subclass that overrides keys() and items() may return views of its own.
        fwdm_cls = cls._fwdm_cls
        cls._fwdm_has_dict_views = (fwdm_cls.keys, fwdm_cls.items) in _DICT_VIEW_METHODS
        cls._ensure_inv_cls()
        cls._set_reversed()

    __reversed__: t.ClassVar[ReversedIter[t.Any] | None]
    #: Whether this class's own __reversed__ was computed by :meth:`_set_reversed` rather than declared.
    #: Only ever read from a class's own namespace, see :meth:`_declared_reversed`.
    _reversed_is_computed: t.ClassVar[bool]

    @classmethod
    def _set_reversed(cls) -> None:
        """Set __reversed__ according to whether the backing mappings are reversible,
        unless this class or one of its bases declares it.
        """
        declared = cls._declared_reversed()
        if declared is MISSING:
            backing_reversible = all(issubclass(i, Reversible) for i in (cls._fwdm_cls, cls._invm_cls))
            cls.__reversed__ = _fwdm_reversed if backing_reversible else None
        elif cls.__reversed__ is not declared:
            # A value computed for a base that precedes the declaring class in the MRO shadows the declared one,
            # e.g. bidict's shadows OrderedBidictBase's in `class C(bidict, OrderedBidict)`.
            cls.__reversed__ = declared
        cls._reversed_is_computed = declared is MISSING
        # For keys(), values(), and items(), whose views are reversible if this bidict is.
        cls._reversible = cls.__reversed__ is not None

    @classmethod
    def _declared_reversed(cls) -> t.Any:
        """The __reversed__ declared by the first class in the MRO that declares one, else MISSING.

        A class declares __reversed__ by setting it, to an implementation
        (e.g. OrderedBidictBase's) or to None to opt out of reversed().
        Values that :meth:`_set_reversed` computed are skipped wherever they are in the MRO:
        they must neither shadow a declared one nor stop a subclass from computing its own.
        """
        mro = cls.__mro__
        # Stop before BidictBase: its own __reversed__ is computed, and Mapping's (None) is a default, not an opt-out.
        for c in mro[: mro.index(BidictBase)]:
            ns = vars(c)
            impl = ns.get('__reversed__', MISSING)
            # Check the value too: one assigned to the class after _set_reversed() ran is declared, unless
            # it's one that _set_reversed() itself assigns (None or _fwdm_reversed), which can't be told apart.
            computed = ns.get('_reversed_is_computed') and (impl is _fwdm_reversed or impl is None)
            if impl is not MISSING and not computed:
                return impl
        return MISSING

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
        Items passed via positional arg are processed first,
        followed by any items passed via keyword argument.
        Any duplication encountered along the way
        is handled as per :attr:`on_dup`.
        A falsy positional arg is treated as empty, without being iterated,
        so as is usual for containers, it must be falsy only when it is empty.
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
        return BidictValuesView(self.inverse) if self._reversible else _NonReversibleBidictValuesView(self.inverse)

    @override
    def keys(self) -> KeysView[KT]:
        """A set-like object providing a view on the contained keys.

        When *b._fwdm* is a :class:`dict`, *b.keys()* returns its *dict_keys*,
        which behaves exactly the same as *collections.abc.KeysView(b)*, except for

          - offering better performance

          - being reversible

          - having a .mapping attribute in Python 3.10+
            that exposes a mappingproxy to *b._fwdm*.

        A :class:`dict` subclass gets the same treatment if its *keys()* and *items()*
        are those of :class:`dict` or :class:`collections.OrderedDict`. Any other backing
        mapping, including a :class:`dict` subclass with views of its own (which need not
        behave like *dict_keys*, e.g. *sortedcontainers.SortedDict*'s set operations return
        a *SortedSet*), gets bidict's own view of this bidict instead,
        which is reversible if this bidict is.
        """
        if self._fwdm_has_dict_views:
            return self._fwdm.keys()
        return _KeysView(self) if self._reversible else _NonReversibleKeysView(self)

    @override
    def items(self) -> ItemsView[KT, VT]:
        """A set-like object providing a view on the contained items.

        When *b._fwdm* is a :class:`dict`, *b.items()* returns its *dict_items*,
        which behaves exactly the same as *collections.abc.ItemsView(b)*, except for:

          - offering better performance

          - being reversible

          - having a .mapping attribute in Python 3.10+
            that exposes a mappingproxy to *b._fwdm*

          - returning False from membership tests of anything but a 2-tuple,
            for which *collections.abc.ItemsView(b)* may raise,
            or return True (e.g. for a list *[key, value]*).

        See :meth:`keys` for how backing mappings that are not exactly dicts are handled.
        """
        if self._fwdm_has_dict_views:
            return self._fwdm.items()
        return _ItemsView(self) if self._reversible else _NonReversibleItemsView(self)

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
        # if it does, everything written before it still has to be undone.
        # Delete the old entries before writing the new ones, so that undoing (in reverse) deletes the new
        # entries before restoring the old ones. A new object may compare equal to the old one it replaces
        # (e.g. under asymmetric __eq__), in which case, while both are in the same backing mapping,
        # deleting or restoring one of them could land on the other's entry instead.
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
        fwdm_set(newkey, newval)
        if unwrites is not None:
            # {0: 1} | {2: 3} => del fwdm[2];  {0: 1} | {0: 3} => fwdm[0] = 1
            unwrites.append((fwdm_del, newkey) if oldval is MISSING else (fwdm_set, newkey, oldval))
        invm_set(newval, newkey)
        if unwrites is not None:
            # {0: 1} | {2: 3} => del invm[3];  {0: 1} | {2: 1} => invm[1] = 0
            unwrites.append((invm_del, newval) if oldkey is MISSING else (invm_set, newval, oldkey))

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
        # Like dict, also accept iterables that only support the legacy __getitem__ protocol. For anything else,
        # iter() raises the appropriate TypeError (without consuming arg) before we've written anything.
        if not isinstance(arg, Iterable) and not hasattr(arg, 'keys'):
            iter(arg)
        if not arg and not kw:
            return
        if on_dup is None:
            on_dup = self.on_dup

        # Fast path when we're empty and updating only from another bidict.
        if not self and not kw and isinstance(arg, BidictBase):
            try:
                self._init_from(arg)
            except BaseException:
                if rollback:  # _init_from() records no unwrites, so go back to empty to fail clean.
                    self._init_from(())
                raise
            # arg has no dups by its own backing mappings' equality, but ours may judge some of its items equal
            # (e.g. case-insensitively), collapsing them in one mapping only. If so, start over on the path below.
            if len(self._fwdm) == len(self._invm) == len(arg):
                return
            self._init_from(())

        # In all other cases, for each new item, perform a dup check (raising if necessary), and apply the associated
        # writes we need to perform on our backing _fwdm and _invm mappings. If rollback is enabled, also compute the
        # associated unwrites as we go. If item unpacking, duplication checking, or writing raises while rollback is
        # enabled, apply the accumulated unwrites before re-raising, to ensure that we fail clean.
        # arg may be our own inverse (e.g. b.update(b.inverse)), which shares the backing mappings written to below,
        # so snapshot its items first. (ty doesn't narrow on the type() check, hence the cast.)
        if type(arg) is self._inv_cls and t.cast('BidictBase[KT, VT]', arg)._fwdm is self._invm:
            arg = [*iteritems(arg)]
        write = self._write
        unwrites: Unwrites | None = [] if rollback else None
        try:
            for key, val in iteritems(arg, **kw):
                dedup_result = self._dedup(key, val, on_dup)
                if dedup_result is not None:
                    write(key, val, *dedup_result, unwrites=unwrites)
        except BaseException:
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
        new = self.__class__(other)
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
            mapping = self._mapping
            if not mapping._fwdm_has_dict_views:  # dict view speedup not available, fall back to Set's implementation.
                return getattr(Set, methodname)(self, *args)
            fwdm_dict_view = getattr(mapping._fwdm, self._viewname)()
            fwdm_dict_view_method = getattr(fwdm_dict_view, methodname)
            # When the (single) arg is another ProxiedSetView whose backing mapping has dict views, forward its
            # backing dict_keys/dict_items to the C-level method rather than the arg itself. C-level dict views
            # only interoperate with other C-level dict views, not with arbitrary Set subclasses, so e.g.
            # `dict_keys(ob1).__lt__(ob2.keys())` returns NotImplemented. With both sides returning
            # NotImplemented, Python either raises TypeError (for `<`, `<=`, `>`, `>=`) or falls back to the
            # wrong answer (e.g. identity-based `==`). Note arg's view may differ from self's (keys vs items),
            # so use arg._viewname; this also subsumes the same-type case, where it equals self._viewname.
            if len(args) == 1 and isinstance((arg := args[0]), ProxiedSetView) and arg._mapping._fwdm_has_dict_views:
                arg_dict_view = getattr(arg._mapping._fwdm, arg._viewname)()
                return fwdm_dict_view_method(arg_dict_view)
            return fwdm_dict_view_method(*args)

        method.__name__ = methodname
        method.__qualname__ = f'{cls.__qualname__}.{methodname}'
        return method

    for name in _setmethodnames:
        setattr(cls, name, make_proxy_method(name))


_override_set_methods_to_use_backing_dict(BidictValuesView)
_override_set_methods_to_use_backing_dict(_KeysView)
_override_set_methods_to_use_backing_dict(_ItemsView)


class GeneratedBidictInverse:
    """Base class for dynamically-generated inverse bidict classes."""


#                             * Code review nav *
# ============================================================================
# ← Prev: _abc.py              Current: _base.py            Next: _frozen.py →
# ============================================================================

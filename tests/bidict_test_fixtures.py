# Copyright 2009-2026 Joshua Bronson. All rights reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import annotations

import operator
import pickle
import typing as t
from collections import OrderedDict
from collections import UserDict
from collections.abc import Iterable
from collections.abc import Iterator
from collections.abc import KeysView
from collections.abc import Mapping
from collections.abc import MutableMapping
from collections.abc import Reversible
from collections.abc import ValuesView
from dataclasses import dataclass
from itertools import chain
from itertools import combinations

from sortedcontainers import SortedDict

from bidict import DROP_NEW
from bidict import DROP_OLD
from bidict import ON_DUP_DROP_OLD
from bidict import RAISE
from bidict import BidictBase
from bidict import DuplicationError
from bidict import KeyAndValueDuplicationError
from bidict import KeyDuplicationError
from bidict import MutableBidirectionalMapping
from bidict import OnDup
from bidict import OrderedBidict
from bidict import OrderedBidictBase
from bidict import ValueDuplicationError
from bidict import bidict
from bidict import frozenbidict
from bidict._typing import Maplike
from bidict._typing import MapOrItems
from bidict._typing import override


KT = t.TypeVar('KT')
VT = t.TypeVar('VT')


class SupportsKeysAndGetItem(t.Generic[KT, VT]):
    def __init__(self, *args: t.Any, **kw: t.Any) -> None:
        # This fixture trusts its *args/**kw (typed Any); dict(**kw) yields str keys, so cast to the declared type.
        self._mapping = t.cast('Mapping[KT, VT]', dict(*args, **kw))

    def keys(self) -> KeysView[KT]:
        return self._mapping.keys()

    def __getitem__(self, key: KT) -> VT:
        return self._mapping[key]


class LegacySequence(t.Generic[KT, VT]):
    """A sequence of items that is iterable only via the legacy __getitem__ protocol (no __iter__), as dict allows."""

    def __init__(self, items: Iterable[tuple[KT, VT]] = ()) -> None:
        self._items = list(items)

    def __getitem__(self, index: int) -> tuple[KT, VT]:
        return self._items[index]


class KeysViaGetattr(t.Generic[KT, VT]):
    """A mapping proxy whose keys() is supplied by __getattr__, as with wrapt, lazy-object-proxy, etc.

    dict() treats it as a mapping, since it looks up keys dynamically. But inspect.getattr_static(),
    and so isinstance(..., Maplike) on Python 3.12+, can't see its keys().
    """

    def __init__(self, *args: t.Any, **kw: t.Any) -> None:
        self._mapping = t.cast('Mapping[KT, VT]', dict(*args, **kw))

    def __getattr__(self, name: str) -> t.Any:
        return getattr(self._mapping, name)

    def __getitem__(self, key: KT) -> VT:
        return self._mapping[key]

    def __iter__(self) -> Iterator[KT]:
        return iter(self._mapping)


BB = BidictBase[KT, VT]
BT = type[BidictBase[KT, VT]]
user_bidict_types: list[BT[t.Any, t.Any]] = []

_B = t.TypeVar('_B', bound=BidictBase[t.Any, t.Any])
_BT = t.TypeVar('_BT', bound=type[BidictBase[t.Any, t.Any]])


def pickle_copy(b: _B, protocol: int | None = None) -> _B:
    return pickle.loads(pickle.dumps(b, protocol))


def user_bidict(cls: _BT) -> _BT:
    # Preserve the exact decorated class type (a plain `BT[KT, VT]` return would widen it to BidictBase).
    user_bidict_types.append(cls)
    return cls


@user_bidict
class UserBi(bidict[KT, VT]):
    _fwdm_cls = UserDict
    _invm_cls = UserDict


@user_bidict
class UserOrderedBi(OrderedBidict[KT, VT]):
    _fwdm_cls = UserDict
    _invm_cls = UserDict


@user_bidict
class UserBiNotOwnInv(bidict[KT, VT]):
    """A custom bidict whose inverse class is not itself."""

    _fwdm_cls = dict
    _invm_cls = UserDict


@user_bidict
class UserBiBackedByDictSub(bidict[KT, VT]):
    """A bidict backed by a dict *subclass*, which gets the same native views as a dict."""

    _fwdm_cls = OrderedDict
    _invm_cls = OrderedDict


class ReversibleUserDict(UserDict[KT, VT]):
    """A reversible backing mapping that, unlike e.g. OrderedDict, is not a dict,
    and whose values() view (UserDict's generic one) is not reversible.
    """

    def __reversed__(self) -> Iterator[KT]:
        return reversed(self.data)


@user_bidict
class UserBiBackedByReversibleNonDict(bidict[KT, VT]):
    """A bidict backed by a reversible mapping that is not a dict, which gets generic views rather than native ones."""

    _fwdm_cls = ReversibleUserDict
    _invm_cls = ReversibleUserDict


class ReversibleUserDictWithReversibleValues(ReversibleUserDict[KT, VT]):
    """Like ReversibleUserDict, except that its values() view is reversible too: that of the dict it wraps."""

    @override
    def values(self) -> ValuesView[VT]:
        return self.data.values()


class UserBiBackedByReversibleValues(bidict[KT, VT]):
    """A bidict backed by a mapping that is not a dict, but whose values() view is reversible."""

    _fwdm_cls = ReversibleUserDictWithReversibleValues
    _invm_cls = ReversibleUserDictWithReversibleValues


# Not registered via @user_bidict: SortedDict requires its keys to be orderable against each other,
# which much of the data that the tests over bidict_types use is not.
class UserBiBackedBySortedDict(bidict[KT, VT]):
    """The SortedBidict recipe in docs/extending.rst: backed by a dict subclass with views of its own."""

    _fwdm_cls = SortedDict
    _invm_cls = SortedDict


class UserOrderedBiBackedBySortedDict(OrderedBidict[KT, VT]):
    """An ordered bidict backed by a dict subclass with views of its own."""

    _fwdm_cls = SortedDict
    _invm_cls = SortedDict


@user_bidict
class UserOrderedBiBase(OrderedBidictBase[KT, VT]):
    """An immutable ordered bidict, i.e. an OrderedBidictBase that is not an OrderedBidict.

    Uses a permissive on_dup so that even a bulk __init__ can overwrite an existing item.
    That is what makes the backing mappings' order diverge from the bidict's own order,
    which is otherwise only reachable by mutating an OrderedBidict.
    """

    on_dup = ON_DUP_DROP_OLD


UserBiNotOwnInvInv = UserBiNotOwnInv._inv_cls
assert UserBiNotOwnInvInv is not UserBiNotOwnInv

BTs = tuple[BT[t.Any, t.Any], ...]
builtin_bidict_types: BTs = (bidict, frozenbidict, OrderedBidict)
bidict_types: BTs = (*builtin_bidict_types, *user_bidict_types)
update_arg_types = (*bidict_types, list, dict, iter, SupportsKeysAndGetItem, LegacySequence, KeysViaGetattr)
mutable_bidict_types: BTs = tuple(t for t in bidict_types if issubclass(t, MutableBidirectionalMapping))
assert frozenbidict not in mutable_bidict_types
MBT = type[bidict[KT, VT]] | type[OrderedBidict[KT, VT]]


def should_be_reversible(bi_t: BT[KT, VT]) -> bool:
    # Every ordered bidict is reversible regardless of its backing mappings, since it
    # iterates its linked list rather than them. Any other bidict is reversible exactly
    # when both its backing mappings are.
    if bi_t in builtin_bidict_types or issubclass(bi_t, OrderedBidictBase):
        return True
    return all(issubclass(i, Reversible) for i in (bi_t._fwdm_cls, bi_t._invm_cls))


assert all(not should_be_reversible(bi_t) or issubclass(bi_t, Reversible) for bi_t in bidict_types)


def powerset(iterable: Iterable[t.Any]) -> Iterable[tuple[t.Any, ...]]:
    iterable = tuple(iterable)
    return chain.from_iterable(combinations(iterable, r) for r in range(len(iterable) + 1))


SET_OPS: t.Any = (
    operator.le,
    operator.lt,
    operator.gt,
    operator.ge,
    operator.eq,
    operator.ne,
    operator.and_,
    operator.or_,
    operator.sub,
    operator.xor,
    (lambda x, y: x.isdisjoint(y)),
)


DEFAULT_ON_DUP = OnDup(DROP_OLD, RAISE)


@dataclass
class Oracle(t.Generic[KT, VT]):
    data: dict[KT, VT]
    ordered: bool

    @property
    def data_inv(self) -> dict[VT, KT]:
        return {v: k for (k, v) in self.data.items()}

    def assert_match(self, bi: BidictBase[KT, VT]) -> None:
        assert dict(bi) == self.data
        assert dict(bi.inv) == self.data_inv
        self.assert_items_match(bi)

    def assert_items_match(self, bi: BidictBase[KT, VT]) -> None:
        if self.ordered:
            assert zip_equal(bi.items(), self.data.items())
        else:
            assert bi.items() == self.data.items()

    def clear(self) -> None:
        self.data.clear()

    def pop(self, key: KT) -> VT:
        return self.data.pop(key)

    def popitem(self, last: bool = True) -> tuple[KT, VT]:
        if last:
            return self.data.popitem()
        key = next(iter(self.data))
        return key, self.data.pop(key)

    def put(self, key: KT, val: VT, on_dup: OnDup = DEFAULT_ON_DUP) -> None:
        oldval = self.data.get(key)
        oldkey = self.data_inv.get(val)
        isdupkey = oldval is not None
        isdupval = oldkey is not None
        if isdupkey and isdupval:
            if key == oldkey:  # (key, val) duplicates an existing item -> no-op
                assert val == oldval
                return
            # key and val each duplicate a different existing item.
            if on_dup.val is RAISE:
                raise KeyAndValueDuplicationError(key, val)
            if on_dup.val is DROP_NEW:
                return
            assert on_dup.val is DROP_OLD
        elif isdupkey:
            if on_dup.key is RAISE:
                raise KeyDuplicationError(key)
            if on_dup.key is DROP_NEW:
                return
            assert on_dup.key is DROP_OLD
        elif isdupval:
            if on_dup.val is RAISE:
                raise ValueDuplicationError(val)
            if on_dup.val is DROP_NEW:
                return
            assert on_dup.val is DROP_OLD
        if not self.ordered:
            self.data[key] = val
            self.data.pop(oldkey, None)
            return
        # Ensure insertion order is preserved in the case of a sequence of overwriting updates.
        updated = {}
        for k, v in self.data.items():
            if k == oldkey or v == oldval:
                if k == oldkey and isdupkey and isdupval:
                    continue
                updated[key] = val
            else:
                updated[k] = v
        updated[key] = val
        self.data = updated

    def putall(self, updates: MapOrItems[KT, VT], on_dup: OnDup = DEFAULT_ON_DUP) -> None:
        # https://bidict.readthedocs.io/en/main/basic-usage.html#order-matters
        tmp = self.data.copy()
        items: Iterable[tuple[KT, VT]]
        if isinstance(updates, Mapping):
            items = t.cast('Mapping[KT, VT]', updates).items()
        elif hasattr(updates, 'keys'):  # like dict() and MutableMapping.update()
            maplike = t.cast('Maplike[KT, VT]', updates)
            items = [(key, maplike[key]) for key in maplike.keys()]
        else:
            items = updates
        try:
            for key, val in items:
                self.put(key, val, on_dup)
        except DuplicationError:
            self.data = tmp  # fail clean (no partially-applied updates)
            raise

    def __ior__(self, other: Mapping[KT, VT]) -> dict[KT, VT]:
        self.putall(other)
        return self.data

    def __or__(self, other: Mapping[KT, VT]) -> dict[KT, VT]:
        before = self.data.copy()
        self.putall(other)
        after = self.data
        self.data = before
        return after

    def __ror__(self, other: Mapping[KT, VT]) -> dict[KT, VT]:
        before = self.data.copy()
        self.data = {}
        try:
            self.putall(other)
            self.putall(before)
        except DuplicationError:
            self.data = before
            raise
        after = self.data
        self.data = before
        return after

    def move_to_end(self, key: KT, last: bool = True) -> None:
        val = self.pop(key)
        if last:
            self.put(key, val)
        else:
            self.data = {key: val, **self.data}


def zip_equal(i1: Iterable[t.Any], i2: Iterable[t.Any]) -> bool:
    return all(map(operator.eq, i1, i2))


def invdict(d: dict[KT, VT]) -> dict[VT, KT]:
    return {v: k for (k, v) in d.items()}


def dedup(x: MapOrItems[KT, VT]) -> dict[KT, VT]:
    return invdict(invdict(dict(x)))


@dataclass(frozen=True)
class Tagged:
    """Equal whenever *n* is equal, but each instance is distinguishable by its *tag*.

    Stands in for the realistic case of value-equal objects that carry distinct state,
    e.g. a dataclass whose __eq__ covers only some of its fields.
    """

    n: int
    tag: str = ''

    @override
    def __eq__(self, other: object) -> bool:
        return isinstance(other, Tagged) and self.n == other.n

    @override
    def __hash__(self) -> int:
        return hash(self.n)


class AsymStored:
    """Pathological type equal to AsymLookup instances, but only when on the left-hand side."""

    @override
    def __hash__(self) -> int:
        return 1

    @override
    def __eq__(self, other: object) -> bool:
        return isinstance(other, AsymLookup)


class AsymLookup:
    """Pathological type that is never equal to anything, even when an AsymStored equals it."""

    @override
    def __hash__(self) -> int:
        return 1

    @override
    def __eq__(self, other: object) -> bool:
        return False


class HashFailed(Exception):
    """The exception that :class:`HashFails` raises by default."""


class HashFails:
    """Hashes by identity, except for the calls that fail_after() or fail_on() select, which raise *exc*.

    Stands in for a key or value whose hash can fail at any one of the several times
    a write or removal hashes it, e.g. with a MemoryError or RecursionError.
    """

    def __init__(self, exc: type[BaseException] = HashFailed) -> None:
        self._exc = exc
        self.stop()

    def fail_after(self, n: int = 0) -> t.Self:
        """From now on, every __hash__ call after the next *n* raises."""
        self._calls, self._fails = 0, lambda call: call > n
        return self

    def fail_on(self, n: int) -> t.Self:
        """Only the *n*th __hash__ call from now raises."""
        self._calls, self._fails = 0, lambda call: call == n
        return self

    def stop(self) -> None:
        """Hash normally again."""
        self._calls, self._fails = 0, lambda _: False

    @override
    def __hash__(self) -> int:
        self._calls += 1
        if self._fails(self._calls):
            raise self._exc
        return object.__hash__(self)


bomb = HashFails().fail_after()


BAD_ITEMS = (
    (HashFailed, (bomb, 0)),  # hashing the key raises
    (HashFailed, (0, bomb)),  # hashing the value raises
    (KeyboardInterrupt, (HashFails(KeyboardInterrupt).fail_after(), 0)),  # not an Exception, so must not escape rollback
    (TypeError, (['unhashable'], 0)),
    (ValueError, (1, 2, 'bad len')),
)


class WriteRefused(BaseException):
    """Raised by the backing mappings that :func:`bidict_refusing_nth_write` provides.

    A BaseException rather than an Exception, so that the tests that use it also check that
    rollback is not limited to Exceptions: e.g. a KeyboardInterrupt can arrive at any point.
    """


def bidict_refusing_nth_write(bi_t: BT[t.Any, t.Any], init: Mapping[t.Any, t.Any], n: int) -> BB[t.Any, t.Any]:
    """Return a *bi_t* containing *init* whose nth write from now on raises :class:`WriteRefused`.

    Stands in for a custom bidict's backing mapping that may raise on a write it will not accept,
    e.g. SortedDict's TypeError when a key is not orderable with the keys already contained.

    Both backing mappings are given the same class, so the count spans them
    the way a single _write() does.
    """
    counting = False
    counter = iter(range(1, 1000))

    def tick() -> None:
        if counting and next(counter) == n:
            raise WriteRefused

    class RefusingDict(UserDict[t.Any, t.Any]):
        @override
        def __setitem__(self, key: t.Any, item: t.Any) -> None:
            tick()
            super().__setitem__(key, item)

        @override
        def __delitem__(self, key: t.Any) -> None:
            tick()
            super().__delitem__(key)

        @override
        def popitem(self) -> tuple[t.Any, t.Any]:
            # Python 3.15 gave UserDict a popitem() of its own that goes straight to self.data,
            # bypassing __delitem__ and so escaping the count above. Take MutableMapping's
            # implementation, which removes via __delitem__ on every supported Python.
            return MutableMapping.popitem(self)

    bi_t_refusing = type(f'Refusing{bi_t.__name__}', (bi_t,), {'_fwdm_cls': RefusingDict, '_invm_cls': RefusingDict})
    bi = bi_t_refusing(init)
    counting = True  # writing init above must not count
    return bi


class CaseFoldingDict(UserDict[t.Any, t.Any]):
    """A backing mapping that judges str keys equal ignoring case, unlike the dicts backing a plain bidict."""

    @staticmethod
    def _fold(key: t.Any) -> t.Any:
        return key.casefold() if isinstance(key, str) else key

    @override
    def __setitem__(self, key: t.Any, item: t.Any) -> None:
        super().__setitem__(self._fold(key), item)

    @override
    def __getitem__(self, key: t.Any) -> t.Any:
        return super().__getitem__(self._fold(key))

    @override
    def __delitem__(self, key: t.Any) -> None:
        super().__delitem__(self._fold(key))

    @override
    def __contains__(self, key: object) -> bool:
        return super().__contains__(self._fold(key))

from __future__ import annotations

import typing as t
from functools import partial

from ._dup import DROP_NEW
from ._dup import DROP_OLD
from ._dup import RAISE
from ._dup import OnDup
from ._exc import DuplicationError
from ._exc import KeyAndValueDuplicationError
from ._exc import KeyDuplicationError
from ._exc import ValueDuplicationError
from ._iter import iteritems
from ._typing import KT
from ._typing import MISSING
from ._typing import OKT
from ._typing import OVT
from ._typing import VT
from ._typing import DedupResult
from ._typing import MapOrItems
from ._typing import Unwrite
from ._typing import Write
from ._typing import WriteSpec


def update(
    fwdm: t.MutableMapping[KT, VT],
    invm: t.MutableMapping[VT, KT],
    arg: MapOrItems[KT, VT],
    kw: dict[str, VT],
    rollback: bool,
    on_dup: OnDup,
    post_spec_write: t.Callable[..., WriteSpec] | None,
) -> None:
    unwrites: list[Unwrite] = []
    extend_unwrites = unwrites.extend
    for key, val in iteritems(arg, **kw):
        try:
            dedup_result = dedup(fwdm, invm, key, val, on_dup)
        except DuplicationError:
            if rollback:
                for unwrite in reversed(unwrites):
                    unwrite()
            raise
        if dedup_result is None:  # no-op
            continue
        writes, new_unwrites = spec_write(
            fwdm,
            invm,
            key,
            val,
            *dedup_result,
            save_unwrites=rollback,
            post_spec_write=post_spec_write,
        )
        for write in writes:
            write()
        if rollback and new_unwrites:  # save new unwrites in case we need them later
            extend_unwrites(new_unwrites)


def dedup(
    fwdm: t.MutableMapping[KT, VT],
    invm: t.MutableMapping[VT, KT],
    key: KT,
    val: VT,
    on_dup: OnDup,
) -> DedupResult[KT, VT]:
    """Check *key* and *val* for any duplication in *fwdm* and *invm*.

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
    oldval: OVT[VT] = fwdm.get(key, MISSING)
    oldkey: OKT[KT] = invm.get(val, MISSING)
    isdupkey, isdupval = oldval is not MISSING, oldkey is not MISSING
    if isdupkey and isdupval:
        if key == oldkey:
            assert val == oldval
            # (key, val) duplicates an existing item -> no-op.
            return None
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
    # else neither isdupkey nor isdupval.
    return oldkey, oldval


def spec_write(
    fwdm: t.MutableMapping[KT, VT],
    invm: t.MutableMapping[VT, KT],
    newkey: KT,
    newval: VT,
    oldkey: OKT[KT],
    oldval: OVT[VT],
    save_unwrites: bool,
    post_spec_write: t.Callable[..., WriteSpec] | None = None,
) -> WriteSpec:
    """Given (newkey, newval) to insert, return the operations necessary to perform the write.

    *oldkey* and *oldval* are as returned by :meth:`_dedup`.

    If *save_unwrites* is true, also include the inverse operations necessary to undo the write.
    This design allows :meth:`_update` to roll back a partially applied update that fails part-way through
    when necessary. This design also allows subclasses that require additional operations to complete
    a write to easily extend this implementation. For example, :class:`bidict.OrderedBidictBase` calls this
    inherited implementation, and then extends the list of ops returned with additional operations
    needed to keep its internal linked list nodes consistent with its items' order as changes are made.
    """
    fwdm_set, invm_set = fwdm.__setitem__, invm.__setitem__
    fwdm_del, invm_del = fwdm.__delitem__, invm.__delitem__
    writes: list[Write] = [
        partial(fwdm_set, newkey, newval),
        partial(invm_set, newval, newkey),
    ]
    unwrites: list[Unwrite] = []
    if oldval is MISSING and oldkey is MISSING:  # no key or value duplication
        # {0: 1, 2: 3} | {4: 5} => {0: 1, 2: 3, 4: 5}
        if save_unwrites:
            unwrites = [
                partial(fwdm_del, newkey),
                partial(invm_del, newval),
            ]
    elif oldval is not MISSING and oldkey is not MISSING:  # key and value duplication across two different items
        # {0: 1, 2: 3} | {0: 3} => {0: 3}
        writes.extend((
            partial(fwdm_del, oldkey),
            partial(invm_del, oldval),
        ))
        if save_unwrites:
            unwrites = [
                partial(fwdm_set, newkey, oldval),
                partial(invm_set, oldval, newkey),
                partial(fwdm_set, oldkey, newval),
                partial(invm_set, newval, oldkey),
            ]
    elif oldval is not MISSING:  # just key duplication
        # {0: 1, 2: 3} | {2: 4} => {0: 1, 2: 4}
        writes.append(partial(invm_del, oldval))
        if save_unwrites:
            unwrites = [
                partial(fwdm_set, newkey, oldval),
                partial(invm_set, oldval, newkey),
                partial(invm_del, newval),
            ]
    else:
        assert oldkey is not MISSING  # just value duplication
        # {0: 1, 2: 3} | {4: 3} => {0: 1, 4: 3}
        writes.append(partial(fwdm_del, oldkey))
        if save_unwrites:
            unwrites = [
                partial(fwdm_set, oldkey, newval),
                partial(invm_set, newval, oldkey),
                partial(fwdm_del, newkey),
            ]
    if post_spec_write is not None:  # OrderedBidictBase
        post_spec_write(writes, unwrites, newkey, newval, oldkey, oldval, save_unwrites)
    return writes, unwrites

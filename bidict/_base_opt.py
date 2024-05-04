# Copyright 2009-2024 Joshua Bronson. All rights reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Provides a pure Python implementation of :class:`BidictBaseOpt`.

:class:`BidictBaseOpt` was extracted from :class:`_base.BidictBase`
to provide all the code needed for the item insertion hot loop.
This module can thus be rewritten in a faster language
as a drop-in replacement for the implementation below.
"""

from __future__ import annotations

import typing as t

from ._abc import BidirectionalMapping
from ._dup import DROP_NEW
from ._dup import DROP_OLD
from ._dup import RAISE
from ._dup import OnDup
from ._exc import DuplicationError
from ._exc import KeyAndValueDuplicationError
from ._exc import KeyDuplicationError
from ._exc import ValueDuplicationError
from ._typing import KT
from ._typing import MISSING
from ._typing import OKT
from ._typing import OVT
from ._typing import VT
from ._typing import DedupResult
from ._typing import ItemsIter
from ._typing import Unwrites


class BidictBaseOpt(BidirectionalMapping[KT, VT]):
    _fwdm: t.MutableMapping[KT, VT]  #: the backing forward mapping (*key* → *val*)
    _invm: t.MutableMapping[VT, KT]  #: the backing inverse mapping (*val* → *key*)

    def _insert_hotloop(self, items: ItemsIter[KT, VT], rollback: bool, on_dup: OnDup) -> None:
        unwrites: Unwrites | None = [] if rollback else None
        for key, val in items:
            try:
                dedup_result = self._dedup(key, val, on_dup)
            except DuplicationError:
                if unwrites is not None:
                    for fn, *args in reversed(unwrites):
                        fn(*args)
                raise
            if dedup_result is not None:
                self._write(key, val, *dedup_result, unwrites=unwrites)

    def _dedup(self, key: KT, val: VT, on_dup: OnDup) -> DedupResult[KT, VT]:
        """Check *key* and *val* for any duplication in *self*.

        Handle any duplication as per *on_dup*.

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
        # Always perform the following writes regardless of duplication.
        fwdm_set(newkey, newval)
        invm_set(newval, newkey)
        if oldval is MISSING and oldkey is MISSING:  # no key or value duplication
            # {0: 1, 2: 3} | {4: 5} => {0: 1, 2: 3, 4: 5}
            if unwrites is not None:
                unwrites.extend((
                    (fwdm_del, newkey),
                    (invm_del, newval),
                ))
        elif oldval is not MISSING and oldkey is not MISSING:  # key and value duplication across two different items
            # {0: 1, 2: 3} | {0: 3} => {0: 3}
            fwdm_del(oldkey)
            invm_del(oldval)
            if unwrites is not None:
                unwrites.extend((
                    (fwdm_set, newkey, oldval),
                    (invm_set, oldval, newkey),
                    (fwdm_set, oldkey, newval),
                    (invm_set, newval, oldkey),
                ))
        elif oldval is not MISSING:  # just key duplication
            # {0: 1, 2: 3} | {2: 4} => {0: 1, 2: 4}
            invm_del(oldval)
            if unwrites is not None:
                unwrites.extend((
                    (fwdm_set, newkey, oldval),
                    (invm_set, oldval, newkey),
                    (invm_del, newval),
                ))
        else:
            assert oldkey is not MISSING  # just value duplication
            # {0: 1, 2: 3} | {4: 3} => {0: 1, 4: 3}
            fwdm_del(oldkey)
            if unwrites is not None:
                unwrites.extend((
                    (fwdm_set, oldkey, newval),
                    (invm_set, newval, oldkey),
                    (fwdm_del, newkey),
                ))

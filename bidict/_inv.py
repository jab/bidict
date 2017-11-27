# -*- coding: utf-8 -*-
# Copyright 2017 Joshua Bronson. All Rights Reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""TODO"""

from weakref import ref

from .compat import PY2, izip


_ATTRS = [
    # from bidict.BidirectionalMapping
    '__inverted__',
    # from bidict.frozenbidict
    'fwdm',
    'invm',
    'on_dup_key',
    'on_dup_val',
    'on_dup_kv',
    '__repr__',
    '__eq__',
    '__ne__',
    '__hash__',
    '_pop',
    '_put',
    '_clear',
    '_become',
    '_update',
    '_update_with_rollback',
    '_undo_write',
    '_dedup_item',
    '_isdupitem',
    '_write_item',
    '_itemsview',
    'copy',
    '__copy__',
    '__len__',
    '__iter__',
    '__getitem__',
    'keys',
    'values',
    'items',
    '__contains__',
    'get',
    # from bidict.bidict
    '__setitem__',
    '__delitem__',
    'pop',
    'put',
    'putall',
    'forceput',
    'popitem',
    'update',
    'forceupdate',
    'setdefault',
    'clear',
    # from bidict.OrderedBidict
    'sntl',
    '__reversed__',
    'equals_order_sensitive',
    'move_to_end',
    # from bidict.namedbidict
    '__reduce__',
    '_namedbidict_getfwd',
    '_namedbidict_getinv',
]

if PY2:
    _ATTRS.extend([
        'iterkeys',
        'itervalues',
        'iteritems',
        'viewkeys',
        'viewvalues',
        'viewitems',
    ])


def _get_attr(cls, name, _cache={}):  # pylint: disable=W0102
    key = (cls, name)
    try:
        return _cache[key]
    except KeyError:
        attr = _cache[key] = getattr(cls, name, None)
        return attr


class InvBase(ref):
    """TODO"""


def _make_inv_cls(bidict_cls):

    class _BidictInv(InvBase):

        INV_CLS = bidict_cls

        def __init__(self, bi_inst):
            """TODO"""
            self._invm = bi_inst._fwdm  # pylint: disable=protected-access
            self._fwdm = bi_inst._invm  # pylint: disable=protected-access
            if hasattr(bi_inst, '_sntl'):
                self._sntl = bi_inst._sntl  # pylint: disable=protected-access
            self._resurrected = None
            super(_BidictInv, self).__init__(bi_inst)

        @property
        def inv(self):
            """TODO"""
            _inv = self()
            if _inv is not None:
                return _inv
            # Our referent was deleted out from under us. Must resurrect.
            # This happens with e.g. ``bidict().inv``.
            if self._resurrected is None:
                items = izip(self._invm, self._fwdm)
                self._resurrected = bidict_cls(items)
            return self._resurrected

        def __call__(self):
            orig = super(_BidictInv, self).__call__()
            if orig is not None:
                return orig
            return self._resurrected

    for name in _ATTRS:
        if not hasattr(bidict_cls, name):
            continue
        attr = _get_attr(bidict_cls, name)
        setattr(_BidictInv, name, attr)

    namedgetfwd = getattr(bidict_cls, '_namedbidict_getfwd', None)
    namedgetinv = getattr(bidict_cls, '_namedbidict_getinv', None)
    if namedgetfwd and namedgetinv:
        setattr(_BidictInv, namedgetfwd.__name__, property(namedgetinv))
        setattr(_BidictInv, namedgetinv.__name__, property(namedgetfwd))

    # Make repr(bi.inv) look just like repr(bidict(bi.inv)):
    _BidictInv.__name__ = bidict_cls.__name__
    # Though this __name__ is more helpful for debugging:
    # _BidictInv.__name__ = bidict_cls.__name__ + 'Inv'
    return _BidictInv


def get_inv_cls(cls, _cache={}):  # pylint: disable=W0102
    """TODO"""
    try:
        return _cache[cls]
    except KeyError:
        inv_cls = _cache[cls] = _make_inv_cls(cls)
        return inv_cls

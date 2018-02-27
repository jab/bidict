# -*- coding: utf-8 -*-
# Copyright 2018 Joshua Bronson. All Rights Reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Provides :func:`bidict.namedbidict`."""

import re

from ._abc import BidirectionalMapping
from ._bidict import bidict


_VALID_NAME = re.compile('^[A-z][A-z0-9_]*$')


def namedbidict(typename, keyname, valname, base_type=bidict):
    """Create a bidict type with custom accessors.

    Analagous to :func:`collections.namedtuple`.
    """
    names = (typename, keyname, valname)
    if not all(map(_VALID_NAME.match, names)) or keyname == valname:
        raise ValueError(names)
    if not issubclass(base_type, BidirectionalMapping):
        raise TypeError(base_type)

    class _Named(base_type):

        __slots__ = ()

        def _getfwd(self):
            return self.inv if self._isinv else self

        def _getinv(self):
            return self if self._isinv else self.inv

        def __reduce__(self):
            return (_make_empty, (typename, keyname, valname, base_type), self.__getstate__())

    bname = base_type.__name__
    fname = valname + '_for'
    iname = keyname + '_for'
    names = dict(typename=typename, bname=bname, keyname=keyname, valname=valname)
    fdoc = u'{typename} forward {bname}: {keyname} → {valname}'.format(**names)
    idoc = u'{typename} inverse {bname}: {valname} → {keyname}'.format(**names)
    setattr(_Named, fname, property(_Named._getfwd, doc=fdoc))  # pylint: disable=protected-access
    setattr(_Named, iname, property(_Named._getinv, doc=idoc))  # pylint: disable=protected-access

    _Named.__name__ = typename
    return _Named


def _make_empty(typename, keyname, valname, base_type):
    """Create a named bidict with the indicated arguments and return an empty instance.
    Used to make :func:`bidict.namedbidict` instances picklable.
    """
    cls = namedbidict(typename, keyname, valname, base_type=base_type)
    return cls()

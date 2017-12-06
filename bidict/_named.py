# -*- coding: utf-8 -*-
# Copyright 2017 Joshua Bronson. All Rights Reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Implements :func:`bidict.namedbidict`."""

import re

from ._bidict import bidict


_LEGALNAMEPAT = '^[A-z][A-z0-9_]*$'
_LEGALNAMERE = re.compile(_LEGALNAMEPAT)


def namedbidict(typename, keyname, valname, base_type=bidict):
    """
    Create a bidict type with custom accessors.

    Analagous to :func:`collections.namedtuple`.
    """
    for name in typename, keyname, valname:
        if not _LEGALNAMERE.match(name):
            raise ValueError('"%s" does not match pattern %s' %
                             (name, _LEGALNAMEPAT))

    getfwd = lambda self: self.inv if self.isinv else self
    getfwd.__name__ = valname + '_for'
    getfwd.__doc__ = u'%s forward %s: %s → %s' % (typename, base_type.__name__, keyname, valname)

    getinv = lambda self: self if self.isinv else self.inv
    getinv.__name__ = keyname + '_for'
    getinv.__doc__ = u'%s inverse %s: %s → %s' % (typename, base_type.__name__, valname, keyname)

    __reduce__ = lambda self: (_make_empty, (typename, keyname, valname, base_type), self.__dict__)
    __reduce__.__name__ = '__reduce__'
    __reduce__.__doc__ = 'helper for pickle'

    __dict__ = {
        getfwd.__name__: property(getfwd),
        getinv.__name__: property(getinv),
        '__reduce__': __reduce__,
    }
    return type(typename, (base_type,), __dict__)


def _make_empty(typename, keyname, valname, base_type):
    """
    Create a named bidict with the indicated arguments and return an empty instance.

    Used to make :func:`bidict.namedbidict` instances picklable.
    """
    cls = namedbidict(typename, keyname, valname, base_type=base_type)
    return cls()

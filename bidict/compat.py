# -*- coding: utf-8 -*-
# Copyright 2018 Joshua Bronson. All Rights Reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


u"""Compatibility helpers.

.. py:attribute:: PY2

    True iff running on Python < 3.

.. py:attribute:: PYPY

    True iff running on PyPy.

.. py:attribute:: viewkeys

    ``viewkeys(x) → x.viewkeys() if PY2 else x.keys()``

.. py:attribute:: viewvalues

    ``viewvalues(x) → x.viewvalues() if PY2 else x.values()``

.. py:attribute:: viewitems

    ``viewitems(x) → x.viewitems() if PY2 else x.items()``

.. py:attribute:: iterkeys

    ``iterkeys(x) → x.iterkeys() if PY2 else iter(x.keys())``

.. py:attribute:: itervalues

    ``itervalues(x) → x.itervalues() if PY2 else iter(x.values())``

.. py:attribute:: iteritems

    ``iteritems(x) → x.iteritems() if PY2 else iter(x.items())``

.. py:attribute:: zip

    ``itertools.izip() if PY2 else zip``

"""

from operator import methodcaller
from platform import python_implementation
from sys import version_info
from warnings import warn

PYMAJOR, PYMINOR = version_info[:2]
PY2 = PYMAJOR < 3
PYPY = python_implementation() == 'PyPy'

# Without the following, pylint gives lots of false positives like
# "Constant name "viewkeys" doesn't conform to UPPER_CASE naming style"
# pylint: disable=invalid-name

if PY2:

    if PYMINOR < 7:  # pragma: no cover
        warn('Python < 2.7 is unsupported.')

    viewkeys = methodcaller('viewkeys')
    viewvalues = methodcaller('viewvalues')
    viewitems = methodcaller('viewitems')

    iterkeys = methodcaller('iterkeys')
    itervalues = methodcaller('itervalues')
    iteritems = methodcaller('iteritems')

    # In Python 3, the collections ABCs were moved into collections.abc, which does not exist in
    # Python 2. Support for importing them directly from collections is dropped in Python 3.8.
    # pylint: disable=unused-import
    from collections import Mapping, MutableMapping, ItemsView, Hashable  # noqa: F401 (unused)

    # abstractproperty deprecated in Python 3.3 in favor of using @property with @abstractmethod.
    # Before 3.3, this silently fails to detect when an abstract property has not been overridden.
    from abc import abstractproperty

    # pylint: disable=unused-import,no-name-in-module,redefined-builtin
    from itertools import izip as zip

else:

    if PYMINOR < 3:  # pragma: no cover
        warn('Python3 < 3.3 is unsupported.')

    viewkeys = methodcaller('keys')
    viewvalues = methodcaller('values')
    viewitems = methodcaller('items')

    def _compose(f, g):
        return lambda x: f(g(x))

    iterkeys = _compose(iter, viewkeys)
    itervalues = _compose(iter, viewvalues)
    iteritems = _compose(iter, viewitems)

    # pylint: disable=unused-import,ungrouped-imports
    from collections.abc import Mapping, MutableMapping, ItemsView, Hashable  # noqa: F401 (unused)

    # pylint: disable=ungrouped-imports
    from abc import abstractmethod
    abstractproperty = _compose(property, abstractmethod)

    zip = zip

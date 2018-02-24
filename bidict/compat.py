# -*- coding: utf-8 -*-
# Copyright 2018 Joshua Bronson. All Rights Reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


u"""Compatibility helpers.

.. py:attribute:: PY2

    True iff running on Python 2.

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

.. py:attribute:: izip

    ``itertools.izip() if PY2 else zip``

"""

from operator import methodcaller
from platform import python_implementation
from sys import version_info
from warnings import warn

PY2 = version_info[0] == 2
PYPY = python_implementation() == 'PyPy'

# Without the following, pylint gives lots of false positives like
# "Constant name "viewkeys" doesn't conform to UPPER_CASE naming style"
# pylint: disable=invalid-name

if PY2:

    if version_info[1] < 7:  # pragma: no cover
        warn('Python < 2.7 is unsupported.')

    viewkeys = methodcaller('viewkeys')
    viewvalues = methodcaller('viewvalues')
    viewitems = methodcaller('viewitems')
    iterkeys = methodcaller('iterkeys')
    itervalues = methodcaller('itervalues')
    iteritems = methodcaller('iteritems')
    from itertools import izip  # pylint: disable=no-name-in-module,unused-import

else:

    if version_info[1] < 3:  # pragma: no cover
        warn('Python3 < 3.3 is unsupported.')

    viewkeys = methodcaller('keys')
    viewvalues = methodcaller('values')
    viewitems = methodcaller('items')

    def _compose(f, g):
        return lambda x: f(g(x))

    iterkeys = _compose(iter, viewkeys)
    itervalues = _compose(iter, viewvalues)
    iteritems = _compose(iter, viewitems)
    izip = zip

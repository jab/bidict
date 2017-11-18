# -*- coding: utf-8 -*-
# Copyright 2017 Joshua Bronson. All Rights Reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

u"""
Compatibility helpers.

    .. py:attribute:: PY2

        True iff running on Python 2.

    .. py:attribute:: PYPY

        True iff running on PyPy.

    .. py:attribute:: Reversible

        ABC for iterable classes that provide a ``__reversed__()`` method,
        as found in Python 3.6's :class:`collections.abc.Reversible`.

    .. py:attribute:: viewkeys

        viewkeys(D) → a set-like object providing a view on D's keys.

    .. py:attribute:: viewvalues

        viewvalues(D) → an object providing a view on D's values.

    .. py:attribute:: viewitems

        viewitems(D) → a set-like object providing a view on D's items.

    .. py:attribute:: iterkeys

        iterkeys(D) → an iterator over the keys of D.

    .. py:attribute:: itervalues

        itervalues(D) → an iterator over the values of D.

    .. py:attribute:: iteritems

        iteritems(D) → an iterator over the (key, value) items of D.

    .. py:attribute:: izip

        Alias for :func:`zip` on Python 3 / ``itertools.izip`` on Python 2.

"""

# pylint: disable-all

from operator import methodcaller
from platform import python_implementation
from sys import version_info

_compose = lambda f, g: lambda x: f(g(x))

PY2 = version_info[0] == 2
PYPY = python_implementation() == 'PyPy'

if PY2:
    assert version_info[1] > 6, 'Python >= 2.7 required'
    viewkeys = methodcaller('viewkeys')
    viewvalues = methodcaller('viewvalues')
    viewitems = methodcaller('viewitems')
    iterkeys = methodcaller('iterkeys')
    itervalues = methodcaller('itervalues')
    iteritems = methodcaller('iteritems')
    from itertools import izip
else:
    viewkeys = methodcaller('keys')
    viewvalues = methodcaller('values')
    viewitems = methodcaller('items')
    iterkeys = _compose(iter, viewkeys)
    itervalues = _compose(iter, viewvalues)
    iteritems = _compose(iter, viewitems)
    izip = zip

try:
    from collections import Reversible
except ImportError:
    from abc import abstractmethod
    from collections import Iterable

    class Reversible(Iterable):
        """Implement :class:`collections.abc.Reversible` for Python < 3.6."""

        __slots__ = ()

        @abstractmethod
        def __reversed__(self):
            while False:
                yield None

        # see "Reversible" in the table at
        # https://docs.python.org/3/library/collections.abc.html#collections-abstract-base-classes
        _subclsattrs = frozenset({'__reversed__', '__iter__'})

        @classmethod
        def __subclasshook__(cls, C):  # noqa: N803 ("argument name should be lowercase")
            """Checks ``C`` for ``__reversed__`` and ``__iter__`` methods."""
            if cls is not Reversible:
                return NotImplemented
            mro = getattr(C, '__mro__', None)
            if mro is None:
                return NotImplemented
            return all(any(B.__dict__.get(i) for B in mro) for i in cls._subclsattrs)

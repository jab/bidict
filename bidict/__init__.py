# -*- coding: utf-8 -*-
# Copyright 2009-2020 Joshua Bronson. All Rights Reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


#==============================================================================
#                    * Welcome to the bidict source code *
#==============================================================================

# Doing a code review? You'll find a "Code review nav" comment like the one
# below at the top and bottom of the most important source files. This provides
# a suggested initial path through the source when reviewing.
#
# Note: If you aren't reading this on https://github.com/jab/bidict, you may be
# viewing an outdated version of the code. Please head to GitHub to review the
# latest version, which contains important improvements over older versions.
#
# Thank you for reading and for any feedback you provide.

#                             * Code review nav *
#==============================================================================
#                             Current: __init__.py            Next: _abc.py →
#==============================================================================


"""The bidirectional mapping library for Python.

bidict by example:

.. code-block:: python

   >>> from bidict import bidict
   >>> element_by_symbol = bidict({'H': 'hydrogen'})
   >>> element_by_symbol['H']
   'hydrogen'
   >>> element_by_symbol.inverse['hydrogen']
   'H'


Please see https://github.com/jab/bidict for the most up-to-date code and
https://bidict.readthedocs.io for the most up-to-date documentation
if you are reading this elsewhere.


.. :copyright: (c) 2009-2020 Joshua Bronson.
.. :license: MPLv2. See LICENSE for details.
"""

# Use private aliases to not re-export these publicly (for Sphinx automodule with imported-members).
from functools import partial as _partial
from types import ModuleType as _ModuleType
from sys import modules as _modules
from warnings import warn as _warn

from . import compat as _c


if _c.PY2:
    raise ImportError('Python 3 is required.')

_warn = _partial(_warn, stacklevel=2)  # pylint: disable=invalid-name

if (_c.PYMAJOR, _c.PYMINOR) < (3, 5):  # pragma: no cover
    _warn('This version of bidict is untested on Python < 3.5 and may not work.')

# The rest of this file only collects functionality implemented in the rest of the
# source for the purposes of exporting it under the `bidict` module namespace.
# pylint: disable=wrong-import-position
# flake8: noqa: F401 (imported but unused)
from ._abc import BidirectionalMapping
from ._base import BidictBase
from ._mut import MutableBidict
from ._bidict import bidict
from ._frozenbidict import frozenbidict
from ._frozenordered import FrozenOrderedBidict
from ._named import namedbidict
from ._orderedbase import OrderedBidictBase
from ._orderedbidict import OrderedBidict
from ._dup import (
    ON_DUP_DEFAULT, ON_DUP_RAISE, ON_DUP_DROP_OLD,
    RAISE, DROP_OLD, DROP_NEW, OnDup, OnDupAction,
)
from ._exc import (
    BidictException,
    DuplicationError, KeyDuplicationError, ValueDuplicationError, KeyAndValueDuplicationError,
)
from ._util import inverted
from .metadata import (
    __author__, __maintainer__, __copyright__, __email__, __credits__, __url__,
    __license__, __status__, __description__, __keywords__, __version__, __version_info__,
)


# Aliases for deprecated constants. TODO: remove in a future release.
OVERWRITE = DROP_OLD
IGNORE = DROP_NEW


class _BidictModuleType(_ModuleType):  # pylint: disable=too-few-public-methods
    """Compatibility shim."""

    def __getattribute__(self, name):
        if name == 'OVERWRITE':
            _warn('bidict.OVERWRITE has been deprecated, use bidict.DROP_OLD instead.')
            return DROP_OLD
        if name == 'IGNORE':
            _warn('bidict.IGNORE has been deprecated, use bidict.DROP_NEW instead.')
            return DROP_NEW
        return object.__getattribute__(self, name)


try:
    _modules[__name__].__class__ = _BidictModuleType
except TypeError:
    pass


#                             * Code review nav *
#==============================================================================
#                             Current: __init__.py            Next: _abc.py →
#==============================================================================

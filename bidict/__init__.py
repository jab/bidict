# Copyright 2009-2022 Joshua Bronson. All Rights Reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


#==============================================================================
#                    * Welcome to the bidict source code *
#==============================================================================

# Reading through the code? You'll find a "Code review nav" comment like the one
# below at the top and bottom of the most important source files. This suggests
# a path through the code that's optimized for familiarizing yourself with it.
#
# You can find the latest version of this code at https://github.com/jab/bidict
# if you're not reading this there already. While there, you can also star and
# watch the project for updates, fork the code, and submit an issue or pull
# request if you have something to contribute. More information can be found
# linked from ../README.rst, and is also displayed on the page linked above.

#                             * Code review nav *
#==============================================================================
#                             Current: __init__.py            Next: _abc.py →
#==============================================================================


"""The bidirectional mapping library for Python.

----

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

----

.. :copyright: (c) 2009-2022 Joshua Bronson.
.. :license: MPLv2. See LICENSE for details.
"""

# Use private aliases to not re-export these publicly (for Sphinx automodule with imported-members).
from sys import version_info as _version_info


if _version_info < (3, 7):  # pragma: no cover
    raise ImportError('Python 3.7+ is required.')

from ._abc import BidirectionalMapping as BidirectionalMapping, MutableBidirectionalMapping as MutableBidirectionalMapping
from ._base import BidictBase as BidictBase, GeneratedBidictInverse as GeneratedBidictInverse, BidictKeysView as BidictKeysView
from ._bidict import MutableBidict as MutableBidict, bidict as bidict
from ._frozenbidict import frozenbidict as frozenbidict
from ._frozenordered import FrozenOrderedBidict as FrozenOrderedBidict
from ._named import NamedBidictBase as NamedBidictBase, namedbidict as namedbidict
from ._orderedbase import OrderedBidictBase as OrderedBidictBase
from ._orderedbidict import OrderedBidict as OrderedBidict
from ._dup import ON_DUP_DEFAULT as ON_DUP_DEFAULT, ON_DUP_RAISE as ON_DUP_RAISE, ON_DUP_DROP_OLD as ON_DUP_DROP_OLD
from ._dup import RAISE as RAISE, DROP_OLD as DROP_OLD, DROP_NEW as DROP_NEW, OnDup as OnDup, OD as OD
from ._exc import BidictException as BidictException, DuplicationError as DuplicationError
from ._exc import KeyDuplicationError as KeyDuplicationError, ValueDuplicationError as ValueDuplicationError, KeyAndValueDuplicationError as KeyAndValueDuplicationError
from ._iter import inverted as inverted
from .metadata import (
    __author__ as __author__, __maintainer__ as __maintainer__, __copyright__ as __copyright__, __email__ as __email__,
    __credits__ as __credits__, __url__ as __url__, __license__ as __license__, __status__ as __status__, __description__ as __description__,
    __keywords__ as __keywords__, __version__ as __version__, __project_urls__ as __project_urls__,
)


#: Alias
OnDupAction = OD


# Set __module__ of re-exported classes to the 'bidict' top-level module name
# so that private/internal submodules are not exposed to users e.g. in repr strings.
_locals = tuple(locals().items())
for _name, _obj in _locals:  # pragma: no cover
    if not getattr(_obj, '__module__', '').startswith('bidict.'):
        continue
    try:
        _obj.__module__ = 'bidict'
    except AttributeError:  # raised when __module__ is read-only (as in OnDup)
        pass


#                             * Code review nav *
#==============================================================================
#                             Current: __init__.py            Next: _abc.py →
#==============================================================================

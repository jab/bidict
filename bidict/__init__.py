# -*- coding: utf-8 -*-
# Copyright 2017 Joshua Bronson. All Rights Reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
Efficient, Pythonic bidirectional map implementation and related functionality.

See https://bidict.readthedocs.io for comprehensive documentation.

.. :copyright: (c) 2017 Joshua Bronson.
.. :license: MPLv2. See LICENSE for details.

"""

from ._common import (BidirectionalMapping, BidictException,
                      DuplicationBehavior, IGNORE, OVERWRITE, RAISE,
                      DuplicationError, KeyDuplicationError, ValueDuplicationError,
                      KeyAndValueDuplicationError)
from ._base import frozenbidict
from ._bidict import bidict
from ._named import namedbidict
from ._ordered import FrozenOrderedBidict, OrderedBidict
from .util import pairs, inverted


__all__ = (
    'BidirectionalMapping',
    'BidictException',
    'DuplicationBehavior',
    'IGNORE',
    'OVERWRITE',
    'RAISE',
    'DuplicationError',
    'KeyDuplicationError',
    'ValueDuplicationError',
    'KeyAndValueDuplicationError',
    'frozenbidict',
    'bidict',
    'namedbidict',
    'FrozenOrderedBidict',
    'OrderedBidict',
    'pairs',
    'inverted',
)


def _get_version():
    """Get the pkg_resources.resource_string from 'VERSION' file."""
    from pkg_resources import resource_string
    try:
        return resource_string(__name__, 'VERSION').decode('ascii').strip()
    except Exception as exc:  # pragma: no cover; pylint: disable=broad-except
        from warnings import warn
        warn('Failed to read/set version: %r' % exc)
        return '0.0.0'


__author__ = 'Joshua Bronson'
__copyright__ = 'Copyright 2017 Joshua Bronson'
__credits__ = [  # see ../docs/thanks.rst.inc
    'Joshua Bronson', 'Michael Arntzenius', 'Francis Carr', 'Gregory Ewing',
    'Raymond Hettinger', 'Jozef Knaperek', 'Daniel Pope', 'Terry Reedy',
    'David Turner', 'Tom Viner']
__license__ = 'MPL 2.0'
__maintainer__ = 'Joshua Bronson'
__email__ = 'jab@math.brown.edu'
__status__ = 'Beta'
__version__ = _get_version()

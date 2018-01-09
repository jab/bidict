# -*- coding: utf-8 -*-
# Copyright 2018 Joshua Bronson. All Rights Reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
Efficient, Pythonic bidirectional map implementation and related functionality.

See https://bidict.readthedocs.io for comprehensive documentation.

.. :copyright: (c) 2018 Joshua Bronson.
.. :license: MPLv2. See LICENSE for details.

"""

# Welcome to the bidict source code.
#
# Beginning a code review? Excellent!
#
# This __init__.py just collects functionality implemented in the other files
# and exports it under the `bidict` module namespace.
#
# If you're looking for an interesting place to head next, check out _abc.py.
# There the BidirectionalMapping abstract base class (ABC) is defined, which
# all the bidirectional mapping types that bidict provides are subclasses of.
#
# ONE MORE THING! If you are not reading this on https://github.com/jab/bidict
# right now, you may not be viewing the latest version of the code. Please head
# to https://github.com/jab/bidict to review the latest version, which contains
# important improvements over older versions.
#
# Thank you for reading =)
# —jab ʕ•●̫•ʔ

from ._abc import BidirectionalMapping
from ._bidict import bidict
from ._dup import DuplicationPolicy, IGNORE, OVERWRITE, RAISE
from ._exc import (
    BidictException, DuplicationError,
    KeyDuplicationError, ValueDuplicationError, KeyAndValueDuplicationError)
from ._frozen import frozenbidict
from ._named import namedbidict
from ._ordered import FrozenOrderedBidict, OrderedBidict
from .metadata import (
    __author__, __maintainer__, __copyright__, __email__, __credits__,
    __license__, __status__, __description__, __version__)
from .util import pairs, inverted


__all__ = (
    '__author__',
    '__maintainer__',
    '__copyright__',
    '__email__',
    '__credits__',
    '__license__',
    '__status__',
    '__description__',
    '__version__',
    'BidirectionalMapping',
    'BidictException',
    'DuplicationPolicy',
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

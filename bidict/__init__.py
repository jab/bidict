# -*- coding: utf-8 -*-

"""
Efficient, Pythonic bidirectional map implementation and related functionality.

See https://bidict.readthedocs.io for comprehensive documentation.

.. :copyright: (c) 2017 Joshua Bronson.
.. :license: MPLv2. See LICENSE for details.

"""

from ._common import (BidirectionalMapping, BidictBase, BidictException,
                      DuplicationBehavior, IGNORE, OVERWRITE, RAISE,
                      DuplicationError, KeyDuplicationError, ValueDuplicationError,
                      KeyAndValueDuplicationError)
from ._bidict import bidict
from ._frozen import FrozenBidictBase, FrozenBidict, FrozenOrderedBidict
from ._loose import LooseBidict, LooseOrderedBidict
from ._named import namedbidict
from ._ordered import OrderedBidictBase, OrderedBidict
from .util import pairs, inverted

__all__ = (
    'BidirectionalMapping',
    'BidictBase',
    'BidictException',
    'DuplicationBehavior',
    'IGNORE',
    'OVERWRITE',
    'RAISE',
    'DuplicationError',
    'KeyDuplicationError',
    'ValueDuplicationError',
    'KeyAndValueDuplicationError',
    'bidict',
    'LooseBidict',
    'LooseOrderedBidict',
    'FrozenBidictBase',
    'FrozenBidict',
    'FrozenOrderedBidict',
    'namedbidict',
    'OrderedBidictBase',
    'OrderedBidict',
    'pairs',
    'inverted',
)

try:
    from pkg_resources import resource_string
    __version__ = resource_string(__name__, 'VERSION').decode('ascii').strip()
# pylint: disable=broad-except
except Exception as exc:  # pragma: no cover
    from warnings import warn
    warn('Failed to read/set version: %r' % exc)

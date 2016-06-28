# -*- coding: utf-8 -*-

"""
Efficient, Pythonic bidirectional map implementation and related functionality.

See https://bidict.readthedocs.io for comprehensive documentation.

.. :copyright: (c) 2016 Joshua Bronson.
.. :license: ISCL. See LICENSE for details.

"""

from ._common import (BidirectionalMapping, BidictException,
                      DuplicationBehavior, IGNORE, OVERWRITE, RAISE,
                      DuplicationError, KeyDuplicationError, ValueDuplicationError,
                      KeyAndValueDuplicationError)
from ._bidict import bidict
from ._loose import loosebidict
from ._frozen import frozenbidict
from ._named import namedbidict
from ._ordered import (OrderedBidirectionalMapping,
                       orderedbidict, frozenorderedbidict, looseorderedbidict)
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
    'bidict',
    'loosebidict',
    'frozenbidict',
    'namedbidict',
    'OrderedBidirectionalMapping',
    'orderedbidict',
    'frozenorderedbidict',
    'looseorderedbidict',
    'pairs',
    'inverted',
)

try:
    from pkg_resources import resource_string
    __version__ = resource_string(__name__, 'VERSION').decode('ascii').strip()
except Exception as e:  # pragma: no cover
    from warnings import warn
    warn('Failed to read/set version: %r' % e)

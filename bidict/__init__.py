# -*- coding: utf-8 -*-

"""
Efficient, Pythonic bidirectional map implementation
and related functionality.

.. :copyright: (c) 2015 Joshua Bronson.
.. :license: ISCL. See LICENSE for details.

"""

from ._common import BidirectionalMapping, BidictException, KeyExistsException, ValueExistsException
from ._bidict import bidict
from ._loose import loosebidict
from ._frozen import frozenbidict
from ._named import namedbidict
from .util import pairs, inverted

__all__ = (
    'BidirectionalMapping',
    'BidictException',
    'KeyExistsException',
    'ValueExistsException',
    'bidict',
    'loosebidict',
    'frozenbidict',
    'namedbidict',
    'pairs',
    'inverted',
)

try:
    from pkg_resources import resource_string
    __version__ = resource_string(__name__, 'VERSION').decode('ascii').strip()
except Exception as e:
    from warnings import warn
    warn('Failed to read/set version: %r' % e)

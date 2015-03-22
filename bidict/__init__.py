"""
Main package which pulls in all bidirectional dict types
and utilities for working with one-to-one mappings.
"""
from ._common import BidirectionalMapping, CollapseException
from ._bidict import bidict
from ._collapsing import collapsingbidict
from ._frozen import frozenbidict
from ._named import namedbidict
from .util import pairs, inverted

__all__ = (
    'BidirectionalMapping',
    'CollapseException',
    'bidict',
    'collapsingbidict',
    'frozenbidict',
    'namedbidict',
    'pairs',
    'inverted',
)

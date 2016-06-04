"""Implements :class:`bidict.orderedbidict` and friends."""

from ._bidict import bidict
from ._common import BidirectionalMapping, _proxied
from ._frozen import frozenbidict
from ._loose import loosebidict
from collections import OrderedDict


class OrderedBidirectionalMapping(BidirectionalMapping):
    """Base class for ordered bidirectional map types."""

    _dcls = OrderedDict

    __reversed__ = _proxied('__reversed__',
                            doc='Like :func:`collections.OrderedDict.__reversed__`.')


class orderedbidict(OrderedBidirectionalMapping, bidict):
    """Mutable, ordered bidict type."""

    def __repr__(self):
        s = repr(self._fwd)
        s = s.replace(self._fwd.__class__.__name__, self.__class__.__name__, 1)
        return s

    def popitem(self, last=True):
        """Similar to :meth:`collections.OrderedDict.popitem`."""
        if not self:
            raise KeyError(self.__class__.__name__ + ' is empty')
        key, val = self._fwd.popitem(last=last)
        del self._inv[val]
        return key, val

    def move_to_end(self, key, last=True):
        """
        Similar to :meth:`collections.OrderedDict.move_to_end`.

        :raises AttributeError: on Python < 3.2.
        """
        val = self[key]
        self._fwd.move_to_end(key, last=last)
        self._inv.move_to_end(val, last=last)


class frozenorderedbidict(OrderedBidirectionalMapping, frozenbidict):
    """Immutable, hashable :class:`bidict.OrderedBidirectionalMapping` type."""


class looseorderedbidict(OrderedBidirectionalMapping, loosebidict):
    """A mutable orderedbidict which always uses forcing put operations."""

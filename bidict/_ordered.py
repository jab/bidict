"""Implements :class:`bidict.orderedbidict` and friends."""

from ._bidict import bidict
from ._common import BidirectionalMapping, _proxied
from ._frozen import frozenbidict
from ._loose import loosebidict
from .util import pairs
from collections import OrderedDict


class OrderedBidirectionalMapping(BidirectionalMapping):
    """Base class for ordered bidirectional map types."""

    _dcls = OrderedDict

    __reversed__ = _proxied('__reversed__',
                            doc='Like ``collections.OrderedDict.__reversed__``.')

    def __repr__(self):
        s = repr(self._fwd)
        s = s.replace(self._fwd.__class__.__name__, self.__class__.__name__, 1)
        return s


class orderedbidict(OrderedBidirectionalMapping, bidict):
    """Mutable, ordered bidict type."""

    def _update_rbf(self, on_dup_key, on_dup_val, on_dup_kv, *args, **kw):
        # No efficient way to restore original ordering of the backing ordered
        # dictionaries after an update that causes some of the items to be
        # removed. So implement rollback-on-failure by making all modifications
        # to a copy of self, and then become the copy if all the modifications
        # succeed.
        copy = self  # Copy-on-write prevents unneeded copying.
        unmodified = True
        for (key, val) in pairs(*args, **kw):
            result = copy._dedup_item(key, val, on_dup_key, on_dup_val, on_dup_kv)
            if result:
                if unmodified:
                    copy = self.copy()
                    unmodified = False
                copy._write_item(key, val, *result)
        if not unmodified:
            # Got here without raising -> become copy.
            self._fwd = copy._fwd
            self._inv = copy._inv
            self.inv._fwd = self._inv
            self.inv._inv = self._fwd

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


class looseorderedbidict(orderedbidict, loosebidict):
    """Mutable, ordered bidict with *OVERWRITE* duplication behaviors by default."""

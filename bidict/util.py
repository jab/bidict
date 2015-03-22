"""
Utilities for working with one-to-one relations.
"""

from .compat import PY2, iteritems
from collections import Iterator


def pairs(*map_or_it, **kw):
    """
    Yields the pairs provided. Signature matches dict's.
    Accepts zero or one positional argument which it first tries iterating over
    as a mapping, and if that fails, falls back to iterating over as
    a sequence, yielding items two at a time.
    Mappings may also be passed as keyword arguments, which will be yielded
    after any passed via positional argument.
    """
    if map_or_it:
        l = len(map_or_it)
        if l != 1:
            raise TypeError('expected at most 1 argument, got %d' % l)
        map_or_it = map_or_it[0]
        try:
            it = iteritems(map_or_it)   # mapping?
        except AttributeError:          #  no
            for (k, v) in map_or_it:    #    -> treat as sequence
                yield (k, v)
        else:                           #  yes
            for (k, v) in it:           #    -> treat as mapping
                yield (k, v)
    for (k, v) in iteritems(kw):
        yield (k, v)


class inverted(Iterator):
    """
    An iterator analogous to the :func:`reversed` built-in.
    Useful for inverting a mapping.
    """
    def __init__(self, data):
        self._data = data

    def __iter__(self):
        """
        First try to call ``__inverted__`` on the wrapped object
        and return the result if the call succeeds
        (i.e. delegate to the object if it supports inverting natively).
        This complements :attr:`bidict.BidirectionalMapping.__inverted__`.

        If the call fails, fall back on calling our own ``__next__`` method.
        """
        try:
            it = self._data.__inverted__
        except AttributeError:
            it = self.__next__
        return it()

    def __next__(self):
        """
        Yields the inverse of each pair yielded by calling :attr:`bidict.pairs`
        on the wrapped object.
        """
        for (k, v) in pairs(self._data):
            yield (v, k)

    # compat
    if PY2:
        next = __next__

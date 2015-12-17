"""Utilities for working with one-to-one relations."""

from .compat import PY2, iteritems
from collections import Iterator


def pairs(*map_or_it, **kw):
    """
    Yield the pairs provided. Signature matches dict's.

    Accepts zero or one positional argument which it first tries iterating over
    as a mapping, and if that fails, falls back to iterating over as
    a sequence, yielding items two at a time.

    Mappings may also be passed as keyword arguments, which will be yielded
    after any passed via positional argument.
    """
    if map_or_it:
        l = len(map_or_it)
        if l != 1:
            raise TypeError('Pass at most 1 positional argument (got %d)' % l)
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
    An iterator yielding the inverses of the provided mappings.

    Works with any object that can be iterated over as a mapping or in pairs
    or that implements its own __inverted__ method.
    """

    def __init__(self, data):
        """Create an :class:`inverted` instance."""
        self._data = data

    def __iter__(self):
        """Create an instance of the actual generator."""
        makeit = getattr(self._data, '__inverted__', self.__next__)
        return makeit()

    def __next__(self):
        """Yield the inverse of each pair in the associated data."""
        for (k, v) in pairs(self._data):
            yield (v, k)

    # compat
    if PY2:
        next = __next__

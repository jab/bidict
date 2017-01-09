"""Utilities for working with one-to-one relations."""

from .compat import iteritems
from collections import Mapping
from itertools import chain


def pairs(*args, **kw):
    """
    Yield the (k, v) pairs provided, as they'd be processed if passed to :class:`dict`.

    If a positional argument is provided,
    its pairs are yielded before those of any keyword arguments.
    The positional argument may be a mapping or sequence or pairs.

    >>> list(pairs({'a': 1}, b=2))
    [('a', 1), ('b', 2)]
    >>> list(pairs([('a', 1), ('b', 2)], b=3))
    [('a', 1), ('b', 2), ('b', 3)]

    :raises TypeError: if more than one positional arg is given.
    """
    it = None
    if args:
        arg = _arg0(args)
        if arg:
            it = iteritems(arg) if isinstance(arg, Mapping) else iter(arg)
    if kw:
        it2 = iteritems(kw)
        it = chain(it, it2) if it else it2
    return it or iter(())


def _arg0(args):
    l = len(args)
    if l != 1:
        raise TypeError('Expected at most 1 positional argument, got %d' % l)
    return args[0]


def inverted(data):
    """
    Yield the inverse items of the provided mapping or iterable.

    Works with any object that can be iterated over as a mapping or in pairs,
    or that implements its own *__inverted__* method.
    """
    inv = getattr(data, '__inverted__', None)
    return inv() if inv else _inverted(data)


def _inverted(data):
    # This is faster than `return imap(tuple, imap(reversed, pairs(data)))`:
    for (k, v) in pairs(data):
        yield (v, k)

# -*- coding: utf-8 -*-
# Copyright 2018 Joshua Bronson. All Rights Reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


"""Useful functions for working with bidirectional mappings and related data."""

from collections import Mapping
from itertools import chain

from .compat import iteritems


def pairs(*args, **kw):
    """
    Yield the (k, v) pairs provided, as they'd be processed if passed to :class:`dict`.

    If a positional argument is provided,
    its pairs are yielded before those of any keyword arguments.
    The positional argument may be a mapping or an iterable of pairs.

    >>> list(pairs({'a': 1}, b=2))
    [('a', 1), ('b', 2)]
    >>> list(pairs([('a', 1), ('b', 2)], b=3))
    [('a', 1), ('b', 2), ('b', 3)]

    :raises TypeError: if more than one positional arg is given.
    """
    argsiter = None
    if args:
        arg = _arg0(args)
        if arg:
            argsiter = iteritems(arg) if isinstance(arg, Mapping) else iter(arg)
    if kw:
        kwiter = iteritems(kw)
        argsiter = chain(argsiter, kwiter) if argsiter else kwiter
    return argsiter or iter(())


def _arg0(args):
    args_len = len(args)
    if args_len != 1:
        raise TypeError('Expected at most 1 positional argument, got %d' % args_len)
    return args[0]


def inverted(obj):
    """
    Yield the inverse items of the provided object.

    If `obj` has a :func:`callable` ``__inverted__`` attribute
    (such as :attr:`bidict.BidirectionalMapping.__inverted__`),
    just return the result of calling the ``__inverted__`` attribute.

    Otherwise, return an iterator that iterates over the items in `obj`,
    inverting each item on the fly.
    See also :attr:`bidict.BidirectionalMapping.__inverted__`
    """
    inv = getattr(obj, '__inverted__', None)
    return inv() if callable(inv) else _inverted_on_the_fly(obj)


def _inverted_on_the_fly(iterable):
    # This is faster than `return imap(tuple, imap(reversed, pairs(iterable)))`:
    for (key, val) in pairs(iterable):
        yield (val, key)

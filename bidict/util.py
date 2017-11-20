# -*- coding: utf-8 -*-
# Copyright 2017 Joshua Bronson. All Rights Reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Utilities for working with one-to-one relations."""

from collections import Mapping
from itertools import chain

from .compat import iteritems


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
    for (key, val) in pairs(data):
        yield (val, key)

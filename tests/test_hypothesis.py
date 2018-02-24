# -*- coding: utf-8 -*-
# Copyright 2018 Joshua Bronson. All Rights Reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Property-based tests using https://hypothesis.readthedocs.io."""

import gc
import pickle
from collections import Mapping, MutableMapping, OrderedDict
from os import getenv
from weakref import ref

import pytest
from hypothesis import assume, given, settings
from hypothesis.strategies import integers, lists, tuples
from bidict import (
    IGNORE, OVERWRITE, RAISE,
    bidict, namedbidict, OrderedBidict,
    frozenbidict, FrozenOrderedBidict)
from bidict.compat import PY2, PYPY, iteritems


settings.register_profile('default', settings(max_examples=200, deadline=None))
settings.load_profile(getenv('HYPOTHESIS_PROFILE', 'default'))


# pylint: disable=C0111
def to_inv_odict(items):
    """Return an OrderedDict with the inverse of each item in ``items``."""
    return OrderedDict((v, k) for (k, v) in items)


def dedup(items):
    """Given some generated items, prune any with duplicated keys or values."""
    pruned = list(iteritems(to_inv_odict(iteritems(to_inv_odict(items)))))
    assume(len(pruned) >= len(items) // 2)
    return pruned


# pylint: disable=C0103
MyNamedBidict = namedbidict('MyNamedBidict', 'key', 'val')
ondupbehaviors = (IGNORE, OVERWRITE, RAISE)
mutable_bidict_types = (bidict, OrderedBidict, MyNamedBidict)
immutable_bidict_types = (frozenbidict, FrozenOrderedBidict)
bidict_types = mutable_bidict_types + immutable_bidict_types
mutating_methods_by_arity = {
    0: ('clear', 'popitem'),
    1: ('__delitem__', 'pop', 'setdefault', 'move_to_end'),
    2: ('__setitem__', 'pop', 'put', 'forceput', 'setdefault'),
    -1: ('update', 'forceupdate'),
}
immutable = integers()
itemlists = lists(tuples(immutable, immutable))
inititems = itemlists.map(dedup)


@pytest.mark.parametrize('B', bidict_types)
def test_slots(B):  # noqa
    """See https://docs.python.org/3/reference/datamodel.html#notes-on-using-slots."""
    stop_at = {object}
    if PY2:
        stop_at.update({Mapping, MutableMapping})  # These don't define __slots__ in Python 2.
    cls_by_slot = {}
    for cls in B.__mro__:
        if cls in stop_at:
            break
        slots = cls.__dict__.get('__slots__')
        assert slots is not None, 'Expected %r to define __slots__' % cls
        for slot in slots:
            seen_at = cls_by_slot.get(slot)
            assert not seen_at, '%r repeats slot %r declared first by %r' % (seen_at, slot, cls)
            cls_by_slot[slot] = cls


@pytest.mark.parametrize('B', bidict_types)
@given(init=inititems)
def test_pickle_roundtrips(B, init):  # noqa
    bi = B(init)
    # Pickling ordered bidicts in Python 2 requires a higher (non-default) protocol version
    ordered = issubclass(B, FrozenOrderedBidict)
    dumps_args = dict(protocol=2) if PY2 and ordered else {}
    dumped = pickle.dumps(bi, **dumps_args)
    roundtripped = pickle.loads(dumped)
    assert roundtripped == bi


@pytest.mark.parametrize('B', bidict_types)
@given(init=inititems)
def test_equality(B, init):  # noqa
    b = B(init)
    d = dict(init)
    o = OrderedDict(init)
    oi = to_inv_odict(iteritems(o))
    di = OrderedDict(oi)
    assert b == d
    assert b == o
    assert not b != d
    assert not b != o
    assert b.inv == oi
    assert b.inv == di
    assert not b.inv != oi
    assert not b.inv != di


@pytest.mark.parametrize('B', bidict_types)
@given(init=inititems)
def test_bidirectional_mappings(B, init):  # noqa
    ordered = issubclass(B, FrozenOrderedBidict)
    C = list if ordered else sorted  # noqa
    b = B(init)
    keysf = C(k for (k, v) in iteritems(b))
    keysi = C(b.inv[v] for (k, v) in iteritems(b))
    assert keysf == keysi
    valsf = C(b[k] for (v, k) in iteritems(b.inv))
    valsi = C(v for (v, k) in iteritems(b.inv))
    assert valsf == valsi


@pytest.mark.parametrize(
    'arity, methodname',
    [(a, m) for (a, ms) in iteritems(mutating_methods_by_arity) for m in ms])
@pytest.mark.parametrize('B', bidict_types)  # noqa
@given(init=inititems, arg1=immutable, arg2=immutable, items=itemlists)
# pylint: disable=too-many-arguments
def test_consistency_after_mutation(arity, methodname, B, init, arg1, arg2, items):
    """
    Call every mutating method on every bidict type that supports it,
    and ensure the bidict is left in a consistent state afterward.
    """
    method = getattr(B, methodname, None)
    if not method:
        return
    args = []
    if arity == -1:
        args.append(items)
    else:
        if arity > 0:
            args.append(arg1)
        if arity > 1:
            args.append(arg2)
    b0 = B(init)
    b1 = b0.copy()
    try:
        method(b1, *args)
    except Exception as exc:  # pylint: disable=W0703
        # method should fail clean, i.e. b1 should be in the same state it was before the call.
        assert b1 == b0, '%r did not fail clean: %r' % (method, exc)
        assert b1.inv == b0.inv, '%r did not fail clean: %r' % (method, exc)
    # Whether method failed or succeeded, b1 should pass consistency checks.
    assert len(b1) == sum(1 for _ in iteritems(b1))
    assert len(b1) == sum(1 for _ in iteritems(b1.inv))
    assert b1 == dict(iteritems(b1))
    assert b1.inv == dict(iteritems(b1.inv))
    assert b1 == to_inv_odict(iteritems(b1.inv))
    assert b1.inv == to_inv_odict(iteritems(b1))


@pytest.mark.parametrize('on_dup_key', ondupbehaviors)
@pytest.mark.parametrize('on_dup_val', ondupbehaviors)
@pytest.mark.parametrize('on_dup_kv', ondupbehaviors)
@pytest.mark.parametrize('B', mutable_bidict_types)
@given(init=inititems, items=itemlists)
def test_putall(on_dup_key, on_dup_val, on_dup_kv, B, init, items):  # noqa
    b0 = B(init)
    expect = b0.copy()
    expectexc = None
    for (k, v) in items:
        try:
            expect.put(k, v, on_dup_key=on_dup_key, on_dup_val=on_dup_val, on_dup_kv=on_dup_kv)
        except Exception as exc:  # pylint: disable=W0703
            expectexc = exc
            expect = b0  # bulk updates fail clean
            break
    check = b0.copy()
    checkexc = None
    try:
        check.putall(items, on_dup_key=on_dup_key, on_dup_val=on_dup_val, on_dup_kv=on_dup_kv)
    except Exception as exc:  # pylint: disable=W0703
        checkexc = exc
    assert type(checkexc) == type(expectexc)  # pylint: disable=C0123
    assert check == expect
    assert check.inv == expect.inv


# ref: http://doc.pypy.org/en/latest/cpython_differences.html#differences-related-to-garbage-collection-strategies  pylint: disable=line-too-long;  # noqa
# "It also means that weak references may stay alive for a bit longer than expected."
@pytest.mark.skipif(PYPY, reason='Weak references on PyPy are not immediately freed')
@pytest.mark.parametrize('B', bidict_types)
def test_no_reference_cycles(B):  # noqa: N803
    gc.disable()
    b = B()
    weak = ref(b)
    assert weak() is not None
    del b
    assert weak() is None
    gc.enable()

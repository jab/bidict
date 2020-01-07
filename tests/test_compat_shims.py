# -*- coding: utf-8 -*-
# Copyright 2009-2020 Joshua Bronson. All Rights Reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Test compatibility shims for deprecated APIs."""

# pylint: disable=invalid-name

import pytest

import bidict as b


def test_OVERWRITE_alias():  # noqa: N802
    """Deprecated bidict.OVERWRITE should be an alias for bidict.DROP_OLD."""
    with pytest.warns(UserWarning):
        assert b.OVERWRITE is b.DROP_OLD


def test_IGNORE_alias():  # noqa: N802
    """Deprecated bidict.IGNORE should be an alias for bidict.DROP_NEW."""
    with pytest.warns(UserWarning):
        assert b.IGNORE is b.DROP_NEW


@pytest.mark.parametrize(
    'init_items, new_item, kw1, kw2', [
        ([(1, 1)], (1, 2), {'on_dup': b.OnDup(key=b.DROP_NEW)}, {'on_dup_key': b.IGNORE}),
        ([(1, 1)], (2, 1), {'on_dup': b.OnDup(val=b.DROP_NEW)}, {'on_dup_val': b.IGNORE}),
        ([(1, 2), (3, 4)], (1, 4), {'on_dup': b.OnDup(kv=b.DROP_NEW)}, {'on_dup_kv': b.IGNORE}),
    ]
)
def test_deprecated_on_dup_kwargs(init_items, new_item, kw1, kw2):
    """Deprecated `on_dup_*` args for put and putall should work like replacement `on_dup` arg."""
    for meth, args in ('put', new_item), ('putall', ([new_item],)):
        bi1 = b.bidict(init_items)
        bi2 = bi1.copy()
        put1 = getattr(bi1, meth)
        put2 = getattr(bi2, meth)
        put1(*args, **kw1)
        with pytest.warns(UserWarning):
            put2(*args, **kw2)
        assert bi1 == bi2
        with pytest.raises(TypeError):
            put2(*args, on_dup=b.DROP_OLD, **kw2)


def test_deprecated_on_dup_class_attr():
    """Setting deprecated `on_dup_*` class attrs on a bidict subclass same as setting `on_dup`."""
    for attr in ('on_dup_key', 'on_dup_val', 'on_dup_kv'):
        subcls = type('Bidict_' + attr, (b.bidict,), {attr: b.DROP_NEW})
        with pytest.warns(UserWarning):
            bi = subcls()
        assert bi.__class__.on_dup == b.OnDup(**{attr[len('on_dup_'):]: b.DROP_NEW})

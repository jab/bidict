# Copyright 2009-2023 Joshua Bronson. All rights reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from __future__ import annotations
from collections.abc import Mapping, MutableMapping
import sys
import typing as t

import pytest

import bidict


# https://github.com/thisch/pytest-sphinx/issues/5#issuecomment-618072237
@pytest.fixture(autouse=True)
def add_doctest_globals(doctest_namespace: t.MutableMapping[str, t.Any]) -> None:
    doctest_namespace['Mapping'] = Mapping
    doctest_namespace['MutableMapping'] = MutableMapping
    doctest_namespace['pypy'] = sys.implementation.name == 'pypy'
    doctest_namespace.update((i for i in vars(bidict).items() if not i[0].startswith('_')))

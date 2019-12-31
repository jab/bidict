#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright 2009-2020 Joshua Bronson. All Rights Reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# First run all tests that pytest discovers.

"""Run all tests."""

import sys
from functools import reduce
from operator import or_

from pytest import main as pytest_main
from sphinx.cmd.build import main as sphinx_main


TEST_FUNCS = [
    pytest_main,

    # pytest's doctest support doesn't support Sphinx extensions
    # (see https://www.sphinx-doc.org/en/latest/usage/extensions/doctest.html)
    # so †est the code in the Sphinx docs using Sphinx's own doctest support.
    lambda: sphinx_main('-b doctest -d docs/_build/doctrees docs docs/_build/doctest'.split()),
]

sys.exit(reduce(or_, (f() for f in TEST_FUNCS)))

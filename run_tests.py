#!/usr/bin/env python3
# Copyright 2009-2022 Joshua Bronson. All rights reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
# First run all tests that pytest discovers.

"""Run all tests."""

from functools import partial

from pytest import main as pytest_main
from sphinx.cmd.build import main as sphinx_main


TEST_FUNCS = (
    pytest_main,
    # pytest's doctest support doesn't support Sphinx extensions
    # (see https://www.sphinx-doc.org/en/latest/usage/extensions/doctest.html)
    # so test the code in the Sphinx docs using Sphinx's own doctest support.
    partial(sphinx_main, '-b doctest -d docs/_build/doctrees docs docs/_build/doctest'.split()),
)

raise SystemExit(sum(bool(f()) for f in TEST_FUNCS))  # type: ignore

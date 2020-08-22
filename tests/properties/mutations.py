# -*- coding: utf-8 -*-
# Copyright 2009-2020 Joshua Bronson. All Rights Reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Mutants for pytest-mutagen tests."""

import pytest_mutagen as mg

from bidict import BidictBase, MutableBidict, OrderedBidictBase


mg.trivial_mutations_all(BidictBase)
mg.trivial_mutations_all(OrderedBidictBase)
mg.trivial_mutations_all(MutableBidict)

# -*- coding: utf-8 -*-
# Copyright 2009-2020 Joshua Bronson. All Rights Reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Set up hypothesis."""

from datetime import timedelta
from os import getenv

from hypothesis import settings


MAX_EXAMPLES_DEFAULT = 200
DEADLINE_DEFAULT = 200

SETTINGS = {
    'max_examples': int(getenv('HYPOTHESIS_MAX_EXAMPLES') or MAX_EXAMPLES_DEFAULT),
    'deadline': timedelta(milliseconds=int(getenv('HYPOTHESIS_DEADLINE') or DEADLINE_DEFAULT)),
}
settings.register_profile('custom', **SETTINGS)
settings.load_profile('custom')

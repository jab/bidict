# -*- coding: utf-8 -*-
# Copyright 2009-2018 Joshua Bronson. All Rights Reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Set up hypothesis."""

from os import getenv
from hypothesis import HealthCheck, settings, unlimited


MAX_EXAMPLES_DEFAULT = 200
MAX_EXAMPLES_MORE = MAX_EXAMPLES_DEFAULT * 10
NOCHECK_SLOW = (HealthCheck.hung_test, HealthCheck.too_slow)
PROFILE_DEFAULT = {
    'max_examples': int(getenv('HYPOTHESIS_MAX_EXAMPLES') or MAX_EXAMPLES_DEFAULT),
    'deadline': None,
    'timeout': unlimited,
    # Enabling coverage slows down hypothesis.
    'suppress_health_check': NOCHECK_SLOW if getenv('COVERAGE') else (),
}
PROFILE_MORE_EXAMPLES = dict(
    PROFILE_DEFAULT,
    max_examples=int(getenv('HYPOTHESIS_MAX_EXAMPLES') or MAX_EXAMPLES_MORE),
    suppress_health_check=NOCHECK_SLOW,
)
settings.register_profile('DEFAULT', **PROFILE_DEFAULT)
settings.register_profile('MORE_EXAMPLES', **PROFILE_MORE_EXAMPLES)


def load_profile(name=getenv('HYPOTHESIS_PROFILE', 'DEFAULT')):
    """Load the Hypothesis profile with the given name."""
    settings.load_profile(name)

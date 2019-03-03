# -*- coding: utf-8 -*-
# Copyright 2009-2019 Joshua Bronson. All Rights Reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Set up hypothesis."""

from os import getenv
from hypothesis import HealthCheck, settings, unlimited


MAX_EXAMPLES_DEFAULT = 200
NOCHECK_SLOW = (HealthCheck.hung_test, HealthCheck.too_slow)
PROFILE_DEFAULT = {
    'max_examples': int(getenv('HYPOTHESIS_MAX_EXAMPLES') or MAX_EXAMPLES_DEFAULT),
    'deadline': None,
    'timeout': unlimited,
    'suppress_health_check': NOCHECK_SLOW,
}
PROFILE_MORE_EXAMPLES = dict(
    PROFILE_DEFAULT,
    max_examples=int(getenv('HYPOTHESIS_MAX_EXAMPLES') or MAX_EXAMPLES_DEFAULT * 10),
    suppress_health_check=NOCHECK_SLOW,
)
settings.register_profile('default', **PROFILE_DEFAULT)
settings.register_profile('more-examples', **PROFILE_MORE_EXAMPLES)


def load_profile(name=getenv('HYPOTHESIS_PROFILE') or 'default'):
    """Load the Hypothesis profile with the given name."""
    settings.load_profile(name)

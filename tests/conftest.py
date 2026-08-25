# Copyright 2009-2026 Joshua Bronson. All rights reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from hypothesis import settings


# deadline=None because hypothesis times each call in wall-clock, and the first call of any test
# can spend a few hundred ms on warm-up that later calls do not, which can trip the 200ms default
# when the machine is loaded.
settings.register_profile('less-examples', deadline=None, max_examples=200, stateful_step_count=100)
settings.register_profile('more-examples', deadline=None, max_examples=500, stateful_step_count=200)

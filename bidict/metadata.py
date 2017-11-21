# -*- coding: utf-8 -*-
# Copyright 2017 Joshua Bronson. All Rights Reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Define bidict package metadata."""


def _get_version(fallback=u'0.0.0.version_not_found'):
    """Return bidict version via pkg_resources, or fallback if not found."""
    from pkg_resources import get_distribution, DistributionNotFound
    try:
        return get_distribution('bidict').version
    except DistributionNotFound:  # pragma: no cover
        return fallback


__author__ = u'Joshua Bronson'
__maintainer__ = u'Joshua Bronson'
__copyright__ = u'Copyright 2017 Joshua Bronson'
__email__ = u'jab@math.brown.edu'

# see ../docs/thanks.rst.inc
__credits__ = [i.strip() for i in u"""
Joshua Bronson, Michael Arntzenius, Francis Carr, Gregory Ewing, Raymond Hettinger, Jozef Knaperek,
Daniel Pope, Terry Reedy, David Turner, Tom Viner
""".split(u',')]

__description__ = u'Efficient, Pythonic bidirectional map implementation and related functionality'

__license__ = u'MPL 2.0'
__status__ = u'Beta'
__version__ = _get_version()

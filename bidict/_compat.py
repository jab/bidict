# -*- coding: utf-8 -*-
# Copyright 2009-2020 Joshua Bronson. All Rights Reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


"""Compatibility helpers."""

import typing


# Without this guard, we get "TypeError: __weakref__ slot disallowed: either we already got one, or __itemsize__ != 0"
# errors on Python 3.6. Apparently this is due to no PEP560 support:
# https://www.python.org/dev/peps/pep-0560/#hacks-and-bugs-that-will-be-removed-by-this-proposal
# > thus allowing generics with __slots__
TYPED_GENERICS_SUPPORT_SLOTS = not hasattr(typing, 'GenericMeta')

# Copyright 2017 Joshua Bronson. All Rights Reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Provides bidict duplication behaviors."""

from ._marker import _Marker


class DuplicationBehavior(_Marker):
    """
    Provide RAISE, OVERWRITE, IGNORE, and ON_DUP_VAL duplication behaviors.

    .. py:attribute:: RAISE

        Raise an exception when a duplication is encountered.

    .. py:attribute:: OVERWRITE

        Overwrite an existing item when a duplication is encountered.

    .. py:attribute:: IGNORE

        Keep the existing item and ignore the new item when a duplication is
        encountered.

    .. py:attribute:: MATCH_ON_DUP_VAL

        Used with *on_dup_kv* to specify that it should match whatever the
        duplication behavior of *on_dup_val* is.
    """


DuplicationBehavior.RAISE = RAISE = DuplicationBehavior('RAISE')
DuplicationBehavior.OVERWRITE = OVERWRITE = DuplicationBehavior('OVERWRITE')
DuplicationBehavior.IGNORE = IGNORE = DuplicationBehavior('IGNORE')
DuplicationBehavior.MATCH_ON_DUP_VAL = MATCH_ON_DUP_VAL = DuplicationBehavior('MATCH_ON_DUP_VAL')

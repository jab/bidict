# -*- coding: utf-8 -*-
# Copyright 2017 Joshua Bronson. All Rights Reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Define bidict package metadata."""


def _get_file_content(filename, fallback='', encoding='utf8'):
    """Return content of indicated file, or fallback if not found."""
    # pragma: no cover
    try:
        from pkg_resources import resource_string
        return resource_string('bidict', filename).decode(encoding)
    except:  # noqa: E722; pylint: disable=bare-except
        pass
    # See ../setup.py
    bidict_setuppy = globals().get('__BIDICT_SETUPPY__FILE__')
    if not bidict_setuppy:
        return fallback
    from os.path import join, dirname, realpath
    from io import open  # pylint: disable=redefined-builtin
    thisdir = dirname(realpath(bidict_setuppy))
    fpath = realpath(join(thisdir, filename))
    if not fpath.startswith(thisdir):
        return fallback
    try:
        with open(fpath, encoding=encoding) as fstream:
            return fstream.read()
    except:  # noqa: E722; pylint: disable=bare-except
        return fallback


__author__ = 'Joshua Bronson'
__maintainer__ = 'Joshua Bronson'
__copyright__ = 'Copyright 2017 Joshua Bronson'
__email__ = 'jab@math.brown.edu'

# see ../docs/thanks.rst.inc
__credits__ = [
    'Joshua Bronson', 'Michael Arntzenius', 'Francis Carr', 'Gregory Ewing',
    'Raymond Hettinger', 'Jozef Knaperek', 'Daniel Pope', 'Terry Reedy',
    'David Turner', 'Tom Viner']

__license__ = 'MPL 2.0'
__status__ = 'Beta'

__long_description__ = _get_file_content('README.rst').replace(
    ':doc:', '(doc:)'  # :doc: breaks long_description rendering on PyPI
) or 'See https://bidict.readthedocs.io'

__version__ = _get_file_content('VERSION').strip() or '0.0.0.version_not_found'

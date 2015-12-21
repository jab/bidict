"""Python 2/3 compatibility helpers."""

from sys import version_info

PY2 = version_info[0] == 2
if PY2:  # pragma: no cover
    assert version_info[1] > 6, 'Python >= 2.7 required'

if PY2:  # pragma: no cover
    iteritems = lambda x: x.iteritems()
    viewitems = lambda x: x.viewitems()
else:  # pragma: no cover
    iteritems = lambda x: iter(x.items())
    viewitems = lambda x: x.items()

iteritems.__doc__ = 'Python 2/3 compatible iteritems'
viewitems.__doc__ = 'Python 2/3 compatible viewitems'

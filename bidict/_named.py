"""Implements :class:`bidict.namedbidict`."""

from ._bidict import bidict
from re import compile as compile_re


_LEGALNAMEPAT = '^[a-zA-Z][a-zA-Z0-9_]*$'
_LEGALNAMERE = compile_re(_LEGALNAMEPAT)


def _empty_namedbidict(mapname, fwdname, invname):
    """
    Create an empty instance of a custom bidict.

    Used to make :func:`bidict.namedbidict` instances picklable.
    """
    return namedbidict(mapname, fwdname, invname)()


def namedbidict(mapname, fwdname, invname, base_type=bidict):
    """
    Create a custom named bidict types.

    Analagous to :func:`collections.namedtuple`.
    """
    for name in mapname, fwdname, invname:
        if not _LEGALNAMERE.match(name):
            raise ValueError('"%s" does not match pattern %s' %
                             (name, _LEGALNAMEPAT))

    for_fwd = invname + '_for'
    for_inv = fwdname + '_for'
    __dict__ = {for_fwd: property(lambda self: self),
                for_inv: base_type.inv}

    custombidict = type(mapname, (base_type,), __dict__)

    # support pickling
    custombidict.__reduce__ = lambda self: \
        (_empty_namedbidict, (mapname, fwdname, invname), self.__dict__)

    return custombidict

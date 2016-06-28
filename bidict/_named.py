# -*- coding: utf-8 -*-

"""Implements :class:`bidict.namedbidict`."""

from ._bidict import bidict
from re import compile as compile_re


_LEGALNAMEPAT = '^[a-zA-Z][a-zA-Z0-9_]*$'
_LEGALNAMERE = compile_re(_LEGALNAMEPAT)


def namedbidict(typename, keyname, valname, base_type=bidict):
    """
    Create a bidict type with custom accessors.

    Analagous to :func:`collections.namedtuple`.
    """
    for name in typename, keyname, valname:
        if not _LEGALNAMERE.match(name):
            raise ValueError('"%s" does not match pattern %s' %
                             (name, _LEGALNAMEPAT))

    getfwd = lambda self: self
    getfwd.__name__ = valname + '_for'
    getfwd.__doc__ = '%s forward %s: %s → %s' % (typename, base_type.__name__, keyname, valname)

    getinv = lambda self: self.inv
    getinv.__name__ = keyname + '_for'
    getinv.__doc__ = '%s inverse %s: %s → %s' % (typename, base_type.__name__, valname, keyname)

    __reduce__ = lambda self: (_make_empty, (typename, keyname, valname), self.__dict__)
    __reduce__.__name__ = '__reduce__'
    __reduce__.__doc__ = 'helper for pickle'

    __dict__ = {
        getfwd.__name__: property(getfwd),
        getinv.__name__: property(getinv),
        '__reduce__': __reduce__,
    }
    return type(typename, (base_type,), __dict__)


def _make_empty(typename, keyname, valname):
    """
    Create an empty instance of a custom bidict.

    Used to make :func:`bidict.namedbidict` instances picklable.
    """
    named = namedbidict(typename, keyname, valname)
    return named()

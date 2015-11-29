from .compat import PY2, iteritems
from .util import pairs
from collections import Mapping


class BidirectionalMapping(Mapping):
    """
    Mutable and immutable bidict types extend this class,
    which implements all the shared logic.
    Users will typically only interact with subclasses of this class.
    """
    def __init__(self, *args, **kw):
        self._fwd = {}
        self._bwd = {}
        self._update(*args, **kw)
        inv = object.__new__(self.__class__)
        inv._fwd = self._bwd
        inv._bwd = self._fwd
        inv._inv = self
        self._inv = inv
        self._hash = None

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self._fwd)

    __str__ = __repr__

    def __eq__(self, other):
        return self._fwd == other

    def __ne__(self, other):
        return self._fwd != other

    @property
    def inv(self):
        """
        Property providing access to the inverse bidict.
        Can be chained as in: ``B.inv.inv is B``.
        """
        return self._inv

    def __inverted__(self):
        """
        Returns an iterator over the inverse mappings.
        """
        return iteritems(self._bwd)

    def __getitem__(self, key):
        return self._fwd[key]

    def _put(self, key, val):
        oldkey = self._bwd.get(val, _missing)
        oldval = self._fwd.get(key, _missing)
        if key == oldkey and val == oldval:
            return
        if oldkey is not _missing:
            raise ValueExistsException((oldkey, val))
        self._fwd[key] = val
        self._bwd[val] = key
        self._bwd.pop(oldval, None)

    def _update(self, *args, **kw):
        for k, v in pairs(*args, **kw):
            self._put(k, v)

    get = lambda self, k, *args: self._fwd.get(k, *args)
    copy = lambda self: self.__class__(self._fwd)
    get.__doc__ = 'Analogous to dict.get()'
    copy.__doc__ = 'Analogous to dict.copy()'
    __len__ = lambda self: len(self._fwd)
    __iter__ = lambda self: iter(self._fwd)
    __contains__ = lambda self, x: x in self._fwd
    __len__.__doc__ = 'Analogous to dict.__len__()'
    __iter__.__doc__ = 'Analogous to dict.__iter__()'
    __contains__.__doc__ = 'Analogous to dict.__contains__()'
    keys = lambda self: self._fwd.keys()
    items = lambda self: self._fwd.items()
    keys.__doc__ = 'Analogous to dict.keys()'
    items.__doc__ = 'Analogous to dict.items()'
    values = lambda self: self._bwd.keys()
    values.__doc__ = \
        "B.values() -> a set-like object providing a view on B's values. " \
        'Note that because values of a BidirectionalMapping are also keys ' \
        'of its inverse, this returns a ``dict_keys`` object rather than a ' \
        '``dict_values`` object, conferring set-like benefits.'
    if PY2:
        iterkeys = lambda self: self._fwd.iterkeys()
        viewkeys = lambda self: self._fwd.viewkeys()
        iteritems = lambda self: self._fwd.iteritems()
        viewitems = lambda self: self._fwd.viewitems()
        itervalues = lambda self: self._bwd.iterkeys()
        viewvalues = lambda self: self._bwd.viewkeys()
        iterkeys.__doc__ = dict.iterkeys.__doc__
        viewkeys.__doc__ = dict.viewkeys.__doc__
        iteritems.__doc__ = dict.iteritems.__doc__
        viewitems.__doc__ = dict.viewitems.__doc__
        itervalues.__doc__ = dict.itervalues.__doc__
        viewvalues.__doc__ = values.__doc__.replace('values()', 'viewvalues()')
        values.__doc__ = dict.values.__doc__


class BidictException(Exception):
    """
    Base class for bidict exceptions.
    """

class ValueExistsException(BidictException):
    """
    Raised when an attempt is made to insert a new mapping into a bidict whose
    key maps to the value of an existing mapping, violating the uniqueness
    constraint.
    """

_missing = object()

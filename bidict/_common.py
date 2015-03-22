from .compat import PY2, iteritems, viewitems
from .util import pairs
from collections import Mapping


class BidirectionalMapping(Mapping):
    """
    Mutable and immutable bidict types extend this class,
    which implements all the shared logic.
    Users typically won't need to touch this.
    """
    def __init__(self, *args, **kw):
        self._fwd = {}
        self._bwd = {}
        for (k, v) in pairs(*args, **kw):
            self._put(k, v)
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
        try:
            return viewitems(self) == viewitems(other)
        except:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __invert__(self):
        """
        Called when the unary inverse operator (~) is applied.
        """
        return self._inv

    inv = property(__invert__, doc='Property providing access to the inverse '
                   'bidict. Can be chained as in: ``B.inv.inv is B``')

    def __inverted__(self):
        return iteritems(self._bwd)

    @staticmethod
    def _fwd_slice(slice):
        """
        Raises :class:`TypeError` if the given slice does not have either only
        its start or only its stop set to a non-None value.

        Returns True if only its start is not None and False if only its stop
        is not None.
        """
        if slice.step is not None or \
            (not ((slice.start is None) ^ (slice.stop is None))):
            raise TypeError('Slice must specify only either start or stop')
        return slice.start is not None

    def __getitem__(self, keyorslice):
        """
        Provides a __getitem__ implementation
        which accepts a slice (e.g. ``b[:val]``)
        to allow referencing an inverse mapping.
        A non-slice value (e.g. ``b[key]``)
        is considered a reference to a forward mapping.
        """
        if isinstance(keyorslice, slice):
            # forward lookup (by key): b[key:]
            if self._fwd_slice(keyorslice):
                return self._fwd[keyorslice.start]
            else:  # inverse lookup (by val): b[:val]
                return self._bwd[keyorslice.stop]
        else:  # keyorslice is a key: b[key]
            return self._fwd[keyorslice]

    def _put(self, key, val):
        try:
            oldval = self._fwd[key]
        except KeyError:
            oldval = _sentinel
        try:
            oldkey = self._bwd[val]
        except KeyError:
            oldkey = _sentinel

        if oldval is not _sentinel and oldkey is not _sentinel:
            if key == oldkey and val == oldval:
                return
            raise CollapseException((key, oldval), (oldkey, val))
        elif oldval is not _sentinel:
            del self._bwd[oldval]
        elif oldkey is not _sentinel:
            del self._fwd[oldkey]

        self._fwd[key] = val
        self._bwd[val] = key

    get = lambda self, k, *args: self._fwd.get(k, *args)
    copy = lambda self: self.__class__(self._fwd)
    get.__doc__ = dict.get.__doc__
    copy.__doc__ = dict.copy.__doc__
    __len__ = lambda self: len(self._fwd)
    __iter__ = lambda self: iter(self._fwd)
    __contains__ = lambda self, x: x in self._fwd
    __len__.__doc__ = dict.__len__.__doc__
    __iter__.__doc__ = dict.__iter__.__doc__
    __contains__.__doc__ = dict.__contains__.__doc__
    keys = lambda self: self._fwd.keys()
    items = lambda self: self._fwd.items()
    keys.__doc__ = dict.keys.__doc__
    items.__doc__ = dict.items.__doc__
    values = lambda self: self._bwd.keys()
    values.__doc__ = \
        "D.values() -> a set-like object providing a view on D's values. " \
        'Note that because values of a BidirectionalMapping are also keys, ' \
        'this returns a ``dict_keys`` object rather than a ``dict_values`` ' \
        'object.'
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


class CollapseException(Exception):
    """
    Raised when an attempt is made to insert a new mapping into a bidict that
    would collapse two existing mappings.
    """


_sentinel = object()

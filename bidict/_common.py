"""
Implements :class:`BidirectionalMapping`, the bidirectional map base class.

Also provides related exception classes and collision behaviors.
"""

from .compat import PY2, iteritems
from .util import inverted, pairs
from collections import Mapping, deque


def _proxied(methodname, ivarname='_fwd', doc=None):
    """Make a func that calls methodname on the indicated instance variable."""
    def proxy(self, *args):
        ivar = getattr(self, ivarname)
        meth = getattr(ivar, methodname)
        return meth(*args)
    proxy.__name__ = methodname
    proxy.__doc__ = doc or 'Like :py:meth:`dict.%s`.' % methodname
    return proxy


class CollisionBehavior(object):
    """
    Provide RAISE, OVERWRITE, and IGNORE collision behaviors.

    .. py:attribute:: RAISE

        Raise an exception when a collision is encountered.

    .. py:attribute:: OVERWRITE

        Overwrite an existing item when a collision is encountered.

    .. py:attribute:: IGNORE

        Keep the existing item and ignore the new item when a collision is
        encountered.

    """

    def __init__(self, id):
        """Create a collision behavior with the given *id*."""
        self.id = id

    def __repr__(self):
        return '<%s>' % self.id

CollisionBehavior.RAISE = RAISE = CollisionBehavior('RAISE')
CollisionBehavior.OVERWRITE = OVERWRITE = CollisionBehavior('OVERWRITE')
CollisionBehavior.IGNORE = IGNORE = CollisionBehavior('IGNORE')

_missing = object()

class BidirectionalMapping(Mapping):
    """
    Base class for all provided bidirectional map types.

    Mutable and immutable bidict types extend this class,
    which implements all the shared logic.
    Users will typically only interact with subclasses of this class.

    .. py:attribute:: inv

        The inverse bidict.

    """

    _dcls = dict
    _on_key_coll = OVERWRITE
    _on_val_coll = RAISE

    def __init__(self, *args, **kw):
        """Like :py:meth:`dict.__init__`, but maintaining bidirectionality."""
        self._fwd = self._dcls()  # dictionary of forward mappings
        self._inv = self._dcls()  # dictionary of inverse mappings
        if args or kw:
            self._update(self._on_key_coll, self._on_val_coll, 1, *args, **kw)
        inv = object.__new__(self.__class__)
        inv._fwd = self._inv
        inv._inv = self._fwd
        inv.inv = self
        self.inv = inv

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self._fwd)

    def __eq__(self, other):
        return self._fwd == other

    def __ne__(self, other):
        return not self.__eq__(other)

    def __inverted__(self):
        """Get an iterator over the inverse mappings."""
        return iteritems(self._inv)

    def __getitem__(self, key):
        return self._fwd[key]

    def _update(self, on_key_coll, on_val_coll, atomic, *args, **kw):
        if not args and not kw:
            return

        nodupk_update = nodupv_update = False
        arginv = kwinv = None

        if atomic and (on_key_coll is RAISE or on_val_coll is RAISE):
            # Do an initial scan through the update to check for dupes
            # (in which case we will raise an exception)
            # before doing the subsequent scan below to apply the update.
            # Thus we avoid applying an update only partially if it fails.
            arg = args[0] if args else {}

            if not hasattr(arg, '__len__'):
                # Assume arg is a generator, so we have to allocate a new
                # dict from it to be able to iterate over it multiple times.
                arg = self._dcls(*arg)

            if len(arg) + len(kw) <= 1:
                # Update has most 1 mapping -> no dupes.
                nodupk_update = nodupv_update = True
                arginv = self._dcls(inverted(arg) if arg else {})
                kwinv = {v: k for (k, v) in iteritems(kw)} if kw else {}
            else:
                # Check for dupes within the update and raise if found.
                if on_key_coll is RAISE and arg:
                    arg = _chkdupk(self._dcls, arg, **kw)
                    nodupk_update = True
                if on_val_coll is RAISE and (arg or kw):
                    arginv, kwinv = _chkdupv(self._dcls, arg, **kw)
                    nodupv_update = True

            if self:
                # Check if the update duplicates any existing keys or values.
                update = self._dedup(on_key_coll, on_val_coll, pairs(arg, **kw))
                # Feed update into a 0-length deque to consume it efficiently.
                # This will raise according to the given collision policies.
                deque(update, maxlen=0)

        if not self and nodupk_update and nodupv_update:
            self._inv.update(arginv, **kwinv)
            self._fwd.update(inverted(self._inv))
        else:
            update = pairs(*args, **kw)
            if self or not nodupk_update or not nodupv_update:
                update = self._dedup(on_key_coll, on_val_coll, update)
            update = self._dedup(on_key_coll, on_val_coll, update)
            self._update_overwriting(update)


    def _update_overwriting(self, update):
        _fwd = self._fwd
        _inv = self._inv
        for (k, v) in update:
            _inv.pop(_fwd.pop(k, _missing), None)
            _fwd.pop(_inv.pop(v, _missing), None)
            _fwd[k] = v
            _inv[v] = k

    def _dedup(self, on_key_coll, on_val_coll, update):
        _fwd = self._fwd
        _inv = self._inv
        on_key_coll_raise = on_key_coll is RAISE
        on_val_coll_raise = on_val_coll is RAISE
        on_key_coll_ignore = on_key_coll is IGNORE
        on_val_coll_ignore = on_val_coll is IGNORE
        for (k, v) in update:
            skip = False
            oldv = _fwd.get(k, _missing)
            kcol = oldv is not _missing
            if oldv == v or (kcol and on_key_coll_ignore):
                skip = True
            elif kcol and on_key_coll_raise:
                raise KeyExistsError((k, oldv))

            oldk = _inv.get(v, _missing)
            vcol = oldk is not _missing
            if oldk == k or (vcol and on_val_coll_ignore):
                skip = True
            elif vcol and on_val_coll_raise:
                raise ValueExistsError((oldk, v))

            if not skip:
                yield (k, v)

    def copy(self):
        """Like :py:meth:`dict.copy`."""
        return self.__class__(self._fwd)

    __len__ = _proxied('__len__')
    __iter__ = _proxied('__iter__')
    __contains__ = _proxied('__contains__')
    get = _proxied('get')
    keys = _proxied('keys')
    items = _proxied('items')
    values = _proxied('keys', ivarname='_inv')
    values.__doc__ = \
        "B.values() -> a set-like object providing a view on B's values.\n\n" \
        'Note that because values of a BidirectionalMapping are also keys ' \
        'of its inverse, this returns a *dict_keys* object rather than a ' \
        '*dict_values* object, conferring set-like benefits.'
    if PY2:  # pragma: no cover
        iterkeys = _proxied('iterkeys')
        viewkeys = _proxied('viewkeys')
        iteritems = _proxied('iteritems')
        viewitems = _proxied('viewitems')
        itervalues = _proxied('iterkeys', ivarname='_inv',
                              doc=dict.itervalues.__doc__)
        viewvalues = _proxied('viewkeys', ivarname='_inv',
                              doc=values.__doc__.replace('values()', 'viewvalues()'))
        values.__doc__ = 'Like :py:meth:`dict.values`.'


def _chkdupk(dcls, arg, **kw):
    if arg:
        if isinstance(arg, Mapping):
            if kw:
                d1, d2 = (arg, kw) if len(arg) < len(kw) else (kw, arg)
                for (k, v) in iteritems(d1):
                    v2 = d2.get(k, _missing)
                    if v2 is not _missing and v2 != v:
                        raise KeyNotUniqueError(k)
        else:
            it = pairs(arg)
            arg = dcls()
            for (k, v) in it:
                pv = arg.get(k, _missing)
                if pv == v:
                    continue
                if pv is not _missing:
                    raise KeyNotUniqueError(k)
                if kw:
                    kwv = kw.get(k, _missing)
                    if kwv is not _missing and kwv != v:
                        raise KeyNotUniqueError(k)
                arg[k] = v
    return arg


def _chkdupv(dcls, arg, **kw):
    kwinv = {}
    if kw:
        for (k, v) in iteritems(kw):
            ek = kwinv.get(v, _missing)
            if ek != k:
                if ek is not _missing:
                    raise ValueNotUniqueError(v)
                kwinv[v] = k
    arginv = dcls()
    if arg:
        if isinstance(arg, BidirectionalMapping):
            arginv = arg.inv
            if kw:
                if len(arg) < len(kw):
                    b1, b2, b2inv = arg, kw, kwinv
                else:
                    b1, b2, b2inv = kw, arg, arg.inv
                for (k, v) in iteritems(b1):
                    b2k = b2inv.get(v, _missing)
                    if b2k is not _missing and b2k != k:
                        raise ValueNotUniqueError(v)
        else:
            for (k, v) in pairs(arg):
                pk = arginv.get(v, _missing)
                if pk == k:
                    continue
                if pk is not _missing:
                    raise ValueNotUniqueError(v)
                if kw:
                    kwk = kwinv.get(k, _missing)
                    if kwk is not _missing and kwk != k:
                        raise ValueNotUniqueError(k)
                arginv[v] = k
    return arginv, kwinv


class BidictException(Exception):
    """Base class for bidict exceptions."""


class UniquenessError(BidictException):
    """Base class for exceptions raised when uniqueness is violated."""


class KeyNotUniqueError(UniquenessError):
    """Raised when a given key is not unique."""

    def __str__(self):
        if self.args:
            return 'Key not unique: %r' % self.args[0]
        return repr(self)


class ValueNotUniqueError(UniquenessError):
    """Raised when a given value is not unique."""

    def __str__(self):
        if self.args:
            return 'Value not unique: %r' % self.args[0]
        return repr(self)


class KeyExistsError(KeyNotUniqueError):
    """Raised when attempting to insert an already-existing key."""

    def __str__(self):
        if self.args:
            return 'Key {0!r} exists with value {1!r}'.format(*self.args[0])
        return repr(self)


class ValueExistsError(ValueNotUniqueError):
    """Raised when attempting to insert an already-existing value."""

    def __str__(self):
        if self.args:
            return 'Value {1!r} exists with key {0!r}'.format(*self.args[0])
        return repr(self)

"""
Implements :class:`BidirectionalMapping`, the bidirectional map base class.

Also provides related exception classes and collision behaviors.
"""

from .compat import PY2, iteritems, viewkeys
from .util import pairs
from collections import Mapping


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
            self._update(self._on_key_coll, self._on_val_coll, *args, **kw)
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
        return self._fwd != other

    def __inverted__(self):
        """Get an iterator over the inverse mappings."""
        return iteritems(self._inv)

    def __getitem__(self, key):
        return self._fwd[key]

    def _put(self, key, val, on_key_coll, on_val_coll):
        _fwd = self._fwd
        _inv = self._inv
        missing = object()
        oldkey = _inv.get(val, missing)
        oldval = _fwd.get(key, missing)
        if key == oldkey and val == oldval:
            return
        if oldval is not missing:  # key exists
            if on_key_coll is RAISE:
                # since multiple values can have the same hash value, refer
                # to the existing key via `_inv[oldval]` rather than `key`
                raise KeyExistsError((_inv[oldval], oldval))
            elif on_key_coll is IGNORE:
                return
        if oldkey is not missing:  # val exists
            if on_val_coll is RAISE:
                # since multiple values can have the same hash value, refer
                # to the existing value via `_fwd[oldkey]` rather than `val`
                raise ValueExistsError((oldkey, _fwd[oldkey]))
            elif on_val_coll is IGNORE:
                return
        _fwd.pop(oldkey, None)
        _inv.pop(oldval, None)
        _fwd[key] = val
        _inv[val] = key

    def _update(self, on_key_coll, on_val_coll, *args, **kw):
        if not args and not kw:
            return

        _fwd = self._fwd
        _inv = self._inv
        missing = object()
        updatefwd = self._dcls()
        updateinv = self._dcls()

        for (k, v) in pairs(*args, **kw):
            cont = False
            oldk = _inv.get(v, missing)
            oldv = _fwd.get(k, missing)
            if k == oldk and v == oldv:
                cont = True
            else:
                if oldv is not missing:  # key exists
                    if on_key_coll is RAISE:
                        raise KeyExistsError((_inv[oldv], oldv))
                    elif on_key_coll is IGNORE:
                        cont = True
                if oldk is not missing:  # val exists
                    if on_val_coll is RAISE:
                        raise ValueExistsError((oldk, _fwd[oldk]))
                    elif on_val_coll is IGNORE:
                        cont = True

            newk = updateinv.get(v, missing)
            newv = updatefwd.get(k, missing)
            if newv is not missing:  # new key given twice
                if on_key_coll is RAISE:
                    raise KeyNotUniqueError(k)
                elif on_key_coll is IGNORE:
                    cont = True
            if newk is not missing:  # new val given twice
                if on_val_coll is RAISE:
                    raise ValueNotUniqueError(v)
                elif on_val_coll is IGNORE:
                    cont = True
            if cont:
                continue
            if newv is not missing and on_key_coll is OVERWRITE:
                del updateinv[newv]
            if newk is not missing and on_val_coll is OVERWRITE:
                del updatefwd[newk]
            updatefwd[k] = v
            updateinv[v] = k

        commonkeys = viewkeys(updatefwd) & viewkeys(_fwd)
        for k in commonkeys:
            del _inv[_fwd.pop(k)]

        commonvals = viewkeys(updateinv) & viewkeys(_inv)
        for v in commonvals:
            del _fwd[_inv.pop(v)]

        _fwd.update(updatefwd)
        _inv.update(updateinv)

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


class BidictException(Exception):
    """Base class for bidict exceptions."""


class UniquenessError(BidictException):
    """Base class for KeysNotUniqueError and ValuesNotUniqueError."""


class KeyNotUniqueError(UniquenessError):
    """Raised when not all keys are unique."""

    def __str__(self):
        return 'Key not unique: %r' % self.args[0]


class ValueNotUniqueError(UniquenessError):
    """Raised when not all values are unique."""

    def __str__(self):
        return 'Value not unique: %r' % self.args[0]


class KeyExistsError(KeyNotUniqueError):
    """Raised when attempting to insert a non-unique key."""

    def __str__(self):
        return 'Key {0!r} exists with value {1!r}'.format(*self.args[0])


class ValueExistsError(ValueNotUniqueError):
    """Raised when attempting to insert a non-unique value."""

    def __str__(self):
        return 'Value {1!r} exists with key {0!r}'.format(*self.args[0])

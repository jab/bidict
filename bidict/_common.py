"""
Implements :class:`BidirectionalMapping`, the bidirectional map base class.

Also provides related exception classes and collision behaviors.
"""

from .compat import PY2, iteritems, viewkeys
from .util import inverted, pairs
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

    def __repr__(self):
        return '<CollisionBehavior:%s>' % self.__class__.__name__

class RAISE(CollisionBehavior):
    """Raise an exception when a collision is encountered."""

class OVERWRITE(CollisionBehavior):
    """Overwrite an existing item when a collision is encountered."""

class IGNORE(CollisionBehavior):
    """Ignore the new item when a collision is encountered."""

CollisionBehavior.RAISE = RAISE = RAISE()
CollisionBehavior.OVERWRITE = OVERWRITE = OVERWRITE()
CollisionBehavior.IGNORE = IGNORE = IGNORE()


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
    _default_key_collision_behavior = OVERWRITE
    _default_val_collision_behavior = RAISE
    _missing = object()

    def __init__(self, *args, **kw):
        """Like :py:meth:`dict.__init__`, but maintaining bidirectionality."""
        self._fwd = self._dcls()  # dictionary of forward mappings
        self._inv = self._dcls()  # dictionary of inverse mappings
        if args or kw:
            self._update(self._default_key_collision_behavior,
                         self._default_val_collision_behavior, *args, **kw)
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
        _missing = self._missing
        oldkey = _inv.get(val, _missing)
        oldval = _fwd.get(key, _missing)
        if key == oldkey and val == oldval:
            return
        keyexists = oldval is not _missing
        if keyexists:
            if on_key_coll is RAISE:
                # since multiple values can have the same hash value, refer
                # to the existing key via `_inv[oldval]` rather than `key`
                raise KeyExistsError((_inv[oldval], oldval))
            elif on_key_coll is IGNORE:
                return
        valexists = oldkey is not _missing
        if valexists:
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

        _fwd, _inv, _missing = self._fwd, self._inv, self._missing

        # take fast path if passed only another bidict
        if not kw and args and isinstance(args[0], BidirectionalMapping):
            l = len(args)
            if l != 1:
                raise TypeError('Expected at most 1 argument, got %d' % l)
            updatefwd = self._dcls(args[0]._fwd)
            updateinv = self._dcls(args[0]._inv)
        else:
            if on_key_coll is RAISE:
                items = frozenset(pairs(*args, **kw))
                updatefwd = self._dcls(items)
                if len(items) > len(updatefwd):
                    raise KeysNotUniqueError(items)
            else:
                updatefwd = self._dcls(*args, **kw)
            updateinv = self._dcls(inverted(updatefwd))
            if len(updatefwd) > len(updateinv):
                if on_val_coll is RAISE:
                    raise ValuesNotUniqueError(updatefwd)
                updatefwd = self._dcls(inverted(updateinv))

        common_vals = viewkeys(updateinv) & viewkeys(_inv)
        if common_vals and on_val_coll is RAISE:
            raise ValuesExistError(common_vals)

        common_keys = viewkeys(updatefwd) & viewkeys(_fwd)
        if common_keys and on_key_coll is RAISE:
            raise KeysExistError(common_keys)

        if common_vals:
            if on_val_coll is IGNORE:
                delfwd, delinv = updatefwd, updateinv
            else:  # on_val_coll is OVERWRITE
                delfwd, delinv = _fwd, _inv
            for v in common_vals:
                del delfwd[delinv.pop(v)]

        if common_keys:
            if on_key_coll is IGNORE:
                delfwd, delinv = updatefwd, updateinv
            else:  # on_key_coll is OVERWRITE
                delfwd, delinv = _fwd, _inv
            for k in common_keys:
                del delinv[delfwd.pop(k)]

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


class KeysNotUniqueError(UniquenessError):
    """Raised when not all keys are unique."""

    def __str__(self):
        return 'Keys not unique: %r' % self.args[0]


class ValuesNotUniqueError(UniquenessError):
    """Raised when not all values are unique."""

    def __str__(self):
        return 'Values not unique: %r' % self.args[0]


class KeysExistError(KeysNotUniqueError):
    """Raised when attempting to insert keys which overlap with existing keys."""

    def __str__(self):
        return 'Keys already exist: %r' % self.args[0]


class ValuesExistError(ValuesNotUniqueError):
    """Raised when attempting to insert values which overlap with existing values."""

    def __str__(self):
        return 'Values already exist: %r' % self.args[0]


class KeyExistsError(KeysExistError):
    """Raised when attempting to insert a non-unique key."""

    def __str__(self):
        return 'Key {0!r} exists with value {1!r}'.format(*self.args[0])


class ValueExistsError(ValuesExistError):
    """Raised when attempting to insert a non-unique value."""

    def __str__(self):
        return 'Value {1!r} exists with key {0!r}'.format(*self.args[0])

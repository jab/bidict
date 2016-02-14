"""
Implements :class:`BidirectionalMapping`, the bidirectional map base class.

Also provides related exception classes.
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
        """Get a string representation of this object for use with repr."""
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
        """Get a string representation of this bidict for use with repr."""
        return '%s(%r)' % (self.__class__.__name__, self._fwd)

    def __eq__(self, other):
        """Test for equality with *other*."""
        return self._fwd == other

    def __ne__(self, other):
        """Test for inequality with *other*."""
        return self._fwd != other

    def __inverted__(self):
        """Get an iterator over the inverse mappings."""
        return iteritems(self._inv)

    def __getitem__(self, key):
        """Retrieve the value associated with *key*."""
        return self._fwd[key]

    def _put(self, key, val, key_clbhv, val_clbhv):
        _fwd = self._fwd
        _inv = self._inv
        _missing = self._missing
        oldkey = _inv.get(val, _missing)
        oldval = _fwd.get(key, _missing)
        if key == oldkey and val == oldval:
            return
        keyexists = oldval is not _missing
        if keyexists:
            if key_clbhv is RAISE:
                # since multiple values can have the same hash value, refer
                # to the existing key via `_inv[oldval]` rather than `key`
                raise KeyExistsException((_inv[oldval], oldval))
            elif key_clbhv is IGNORE:
                return
        valexists = oldkey is not _missing
        if valexists:
            if val_clbhv is RAISE:
                # since multiple values can have the same hash value, refer
                # to the existing value via `_fwd[oldkey]` rather than `val`
                raise ValueExistsException((oldkey, _fwd[oldkey]))
            elif val_clbhv is IGNORE:
                return
        _fwd.pop(oldkey, None)
        _inv.pop(oldval, None)
        _fwd[key] = val
        _inv[val] = key

    def _update(self, key_clbhv, val_clbhv, *args, **kw):
        if not args and not kw:
            return

        _fwd, _inv, _missing = self._fwd, self._inv, self._missing

        # take fast path if passed only another bidict
        if not kw and args and isinstance(args[0], BidirectionalMapping):
            updatefwd = self._dcls(args[0]._fwd)
            updateinv = self._dcls(args[0]._inv)
        else:
            if key_clbhv is RAISE:
                items = tuple(pairs(*args, **kw))
                updatefwd = self._dcls(items)
                if len(items) > len(updatefwd):
                    raise KeyExistsException(args, kw)
            else:
                updatefwd = self._dcls(*args, **kw)
            updateinv = self._dcls(inverted(updatefwd))
            if len(updatefwd) > len(updateinv):
                if val_clbhv is RAISE:
                    raise ValueExistsException(args, kw)
                updatefwd = self._dcls(inverted(updateinv))

        common_vals = viewkeys(updateinv) & viewkeys(_inv)
        if common_vals and val_clbhv is RAISE:
            v = next(iter(common_vals))
            raise ValueExistsException((_inv[v], v))

        common_keys = viewkeys(updatefwd) & viewkeys(_fwd)
        if common_keys and key_clbhv is RAISE:
            k = next(iter(common_keys))
            raise KeyExistsException((k, _fwd[k]))

        if common_vals:
            if val_clbhv is IGNORE:
                delfwd, delinv = updatefwd, updateinv
            else:  # val_clbhv is OVERWRITE
                delfwd, delinv = _fwd, _inv
            for v in common_vals:
                del delfwd[delinv.pop(v)]

        if common_keys:
            if key_clbhv is IGNORE:
                delfwd, delinv = updatefwd, updateinv
            else:  # key_clbhv is OVERWRITE
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

    def __repr__(self):  # pragma: no cover
        """Get a string representation of this exception for use with repr."""
        return "<%s '%s'>" % (self.__class__.__name__, self)


class KeyExistsException(BidictException):
    """
    Guards against replacing an existing mapping whose key matches the given.

    Raised when an attempt is made to insert a new mapping into a bidict whose
    value maps to the key of an existing mapping.
    """

    def __str__(self):
        """Get a string representation of this exception for use with str."""
        return 'Key {0!r} exists with value {1!r}'.format(*self.args[0])


class ValueExistsException(BidictException):
    """
    Guards against replacing an existing mapping whose value matches the given.

    Raised when an attempt is made to insert a new mapping into a bidict whose
    key maps to the value of an existing mapping.
    """

    def __str__(self):
        """Get a string representation of this exception for use with str."""
        return 'Value {1!r} exists with key {0!r}'.format(*self.args[0])

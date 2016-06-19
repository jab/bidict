"""
Implements :class:`BidirectionalMapping`, the bidirectional map base class.

Also provides related exception classes and duplication behaviors.
"""

from .compat import PY2, iteritems
from .util import pairs
from collections import Mapping


def _proxied(methodname, ivarname='_fwd', doc=None):
    """Make a func that calls methodname on the indicated instance variable."""
    def proxy(self, *args):
        ivar = getattr(self, ivarname)
        meth = getattr(ivar, methodname)
        return meth(*args)
    proxy.__name__ = methodname
    proxy.__doc__ = doc or 'Like ``dict.%s()``.' % methodname
    return proxy


class DuplicationBehavior(object):
    """
    Provide RAISE, OVERWRITE, and IGNORE duplication behaviors.

    .. py:attribute:: RAISE

        Raise an exception when a duplication is encountered.

    .. py:attribute:: OVERWRITE

        Overwrite an existing item when a duplication is encountered.

    .. py:attribute:: IGNORE

        Keep the existing item and ignore the new item when a duplication is
        encountered.

    """

    def __init__(self, id):
        """Create a duplication behavior with the given *id*."""
        self.id = id

    def __repr__(self):
        return '<%s>' % self.id  # pragma: no cover

DuplicationBehavior.RAISE = RAISE = DuplicationBehavior('RAISE')
DuplicationBehavior.OVERWRITE = OVERWRITE = DuplicationBehavior('OVERWRITE')
DuplicationBehavior.IGNORE = IGNORE = DuplicationBehavior('IGNORE')

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
    _on_dup_key = OVERWRITE
    _on_dup_val = RAISE
    _on_dup_kv = RAISE

    def __init__(self, *args, **kw):
        """Like ``dict.__init__()``, but maintaining bidirectionality."""
        self._fwd = self._dcls()  # dictionary of forward mappings
        self._inv = self._dcls()  # dictionary of inverse mappings
        inv = object.__new__(self.__class__)
        inv._fwd = self._inv
        inv._inv = self._fwd
        inv.inv = self
        self.inv = inv
        if args or kw:
            self._update(True, self._on_dup_key, self._on_dup_val, self._on_dup_kv, *args, **kw)

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self._fwd)

    def __eq__(self, other):
        return self._fwd == other

    def __ne__(self, other):
        return not self.__eq__(other)

    def __inverted__(self):
        """Get an iterator over the items in :attr:`self.inv <inv>`."""
        return iteritems(self._inv)

    def __getitem__(self, key):
        return self._fwd[key]

    def _del(self, key):
        val = self._fwd.pop(key)
        del self._inv[val]
        return val

    def _put(self, key, val, on_dup_key, on_dup_val, on_dup_kv):
        result = _dedup_item(key, val, self._fwd, self._inv, on_dup_key, on_dup_val, on_dup_kv)
        if result:
            self._write_item(key, val, *result)

    def _write_item(self, key, val, isdupkey, isdupval, oldkey, oldval):
        # Only remove old key (val) before writing if we're not about to
        # write the same key (val). Thus if this is an orderedbidict, the
        # item is changed in place rather than moved to the end.
        if isdupkey and oldkey != key:
            del self._fwd[self._inv.pop(oldval)]
        if isdupval and oldval != val:
            # Use pop with defaults in case we just took the branch 2 lines up.
            self._inv.pop(self._fwd.pop(oldkey, _missing), None)
        self._fwd[key] = val
        self._inv[val] = key

    def _update(self, init, on_dup_key, on_dup_val, on_dup_kv, *args, **kw):
        if not args and not kw:
            return
        if not init or RAISE in (on_dup_key, on_dup_val, on_dup_kv):
            # Guarantee failing cleanly: If inserting any item causes an error,
            # only a copy will have been changed.
            copy = self.copy()
            _put = copy._put
            for (k, v) in pairs(*args, **kw):
                _put(k, v, on_dup_key, on_dup_val, on_dup_kv)
            # Got here without raising. Become copy, with the update applied.
            self._fwd = copy._fwd
            self._inv = copy._inv
            self.inv._fwd = self._inv
            self.inv._inv = self._fwd
        else:
            _put = self._put
            for (k, v) in pairs(*args, **kw):
                _put(k, v, on_dup_key, on_dup_val, on_dup_kv)

    def copy(self):
        """Like :py:meth:`dict.copy`."""
        copy = object.__new__(self.__class__)
        copy._fwd = self._fwd.copy()
        copy._inv = self._inv.copy()
        cinv = object.__new__(self.__class__)
        cinv._fwd = copy._inv
        cinv._inv = copy._fwd
        cinv.inv = copy
        copy.inv = cinv
        return copy

    __copy__ = copy
    __len__ = _proxied('__len__')
    __iter__ = _proxied('__iter__')
    __contains__ = _proxied('__contains__')
    get = _proxied('get')
    keys = _proxied('keys')
    items = _proxied('items')
    values = _proxied('keys', ivarname='_inv')
    values.__doc__ = \
        "B.values() -> a set-like object providing a view on B's values.\n\n" \
        'Note that because values of a BidirectionalMapping are also keys\n' \
        'of its inverse, this returns a *dict_keys* object rather than a\n' \
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
        values.__doc__ = 'Like ``dict.values()``.'


def _dedup_item(key, val, fwd, inv, on_dup_key, on_dup_val, on_dup_kv):
    """
    Check *key* and *val* for any duplication in mutually-inverse dictionaries
    *fwd* and *inv*. Handle any duplication as per the given duplication behaviors.

    (key, val) already present is construed as a no-op, not a duplication.

    If duplication is found and the corresponding duplication behavior is
    *RAISE*, raise the appropriate error.

    If duplication is found and the corresponding duplication behavior is
    *IGNORE*, return *None*.

    If duplication is found and the corresponding duplication behavior is
    *OVERWRITE*, or if no duplication is found, return the dedup result
    *(isdupkey, isdupval, oldkey, oldval)*.
    """
    oldval = fwd.get(key, _missing)
    oldkey = inv.get(val, _missing)
    isdupitem = oldval == val
    assert isdupitem == (oldkey == key)
    isdupkey = oldval is not _missing
    isdupval = oldkey is not _missing
    # Rather than pass `key` and `val` to the exceptions raised below, pass
    # `exinv[oldval]` and `fwd[oldkey]` so that the existing item is referred
    # to exactly (hash-equivalence != identity).
    # e.g. hash(0) == hash(False) -> {0: 'foo'}[False] == 'foo'.
    # Thus refer to the existing item as (0, 'foo'), not (False, 'foo').
    if isdupkey and isdupval:
        if isdupitem:  # (k, v) duplicates an existing item.
            if on_dup_kv is RAISE:
                return  # No-op. Never raise in this case.
            elif on_dup_kv is IGNORE:
                return
            # else on_dup_kv is OVERWRITE. Fall through to return on last line.
        else:
            # k and v each duplicate a different existing item.
            if on_dup_kv is RAISE:
                raise KeyAndValueNotUniqueError((inv[oldval], oldval), (oldkey, fwd[oldkey]))
            elif on_dup_kv is IGNORE:
                return
            # else on_dup_kv is OVERWRITE. Fall through to return on last line.
    else:
        if isdupkey:
            if on_dup_key is RAISE:
                raise KeyNotUniqueError((inv[oldval], oldval))
            elif on_dup_key is IGNORE:
                return
            # else on_dup_key is OVERWRITE. Fall through to return on last line.
        elif isdupval:
            if on_dup_val is RAISE:
                raise ValueNotUniqueError((oldkey, fwd[oldkey]))
            elif on_dup_val is IGNORE:
                return
            # else on_dup_val is OVERWRITE. Fall through to return on last line.
        # else neither isdupkey nor isdupval (oldkey and oldval both _missing).
    return isdupkey, isdupval, oldkey, oldval


class BidictException(Exception):
    """Base class for bidict exceptions."""


class UniquenessError(BidictException):
    """Base class for exceptions raised when uniqueness is violated."""


class KeyNotUniqueError(UniquenessError):
    """Raised when a given key is not unique."""

    def __str__(self):
        return ('Key duplicated in item: %r' % self.args) if self.args else ''


class ValueNotUniqueError(UniquenessError):
    """Raised when a given value is not unique."""

    def __str__(self):
        return ('Value duplicated in item: %r' % self.args) if self.args else ''


class KeyAndValueNotUniqueError(KeyNotUniqueError, ValueNotUniqueError):
    """
    Raised when a given item's key and value are not unique.

    That is, its key duplicates that of another item,
    and its value duplicates that of a different other item.
    """

    def __str__(self):
        return ('Key {0[0]!r} and value {1[1]!r} duplicated in items: {0!r}, {1!r}'.format(
            *self.args) if self.args else '')

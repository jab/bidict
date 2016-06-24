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


class _marker(object):
    def __init__(self, id):
        self.id = id

    def __repr__(self):
        return '<%s>' % self.id


class DuplicationBehavior(_marker):
    """
    Provide RAISE, OVERWRITE, and IGNORE duplication behaviors.

    .. py:attribute:: RAISE

        Raise an exception when a duplication is encountered.

    .. py:attribute:: OVERWRITE

        Overwrite an existing item when a duplication is encountered.

    .. py:attribute:: IGNORE

        Keep the existing item and ignore the new item when a duplication is
        encountered.

    .. py:attribute:: ON_DUP_VAL

        Used with *on_dup_kv* to specify that it should match whatever the
        duplication behavior of *on_dup_val* is.

    """

DuplicationBehavior.RAISE = RAISE = DuplicationBehavior('RAISE')
DuplicationBehavior.OVERWRITE = OVERWRITE = DuplicationBehavior('OVERWRITE')
DuplicationBehavior.IGNORE = IGNORE = DuplicationBehavior('IGNORE')
DuplicationBehavior.ON_DUP_VAL = ON_DUP_VAL = DuplicationBehavior('ON_DUP_VAL')


_missing = _marker('MISSING')


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
        result = self._dedup_item(key, val, on_dup_key, on_dup_val, on_dup_kv)
        if result:
            self._write_item(key, val, *result)

    def _dedup_item(self, key, val, on_dup_key, on_dup_val, on_dup_kv):
        """
        Check *key* and *val* for any duplication in self.

        Handle any duplication as per the given duplication behaviors.

        (key, val) already present is construed as a no-op, not a duplication.

        If duplication is found and the corresponding duplication behavior is
        *RAISE*, raise the appropriate error.

        If duplication is found and the corresponding duplication behavior is
        *IGNORE*, return *None*.

        If duplication is found and the corresponding duplication behavior is
        *OVERWRITE*, or if no duplication is found, return the dedup result
        *(isdupkey, isdupval, oldkey, oldval)*.
        """
        fwd = self._fwd
        inv = self._inv
        oldval = fwd.get(key, _missing)
        oldkey = inv.get(val, _missing)
        isdupitem = oldval == val
        assert isdupitem == (oldkey == key)
        isdupkey = oldval is not _missing
        isdupval = oldkey is not _missing
        # Since hash-equivalence != identity, rather than pass `key` and `val` to
        # the exceptions raised below, pass `inv[oldval]` and `fwd[oldkey]` so that
        # existing keys/values are referred to exactly. e.g. hash(0) == hash(False)
        # means that {0: 'foo'}[False] == 'foo'. Refer to the existing item as
        # (0, 'foo'), not (False, 'foo').
        if isdupkey and isdupval:
            if isdupitem:  # (key, val) duplicates an existing item.
                if on_dup_kv is RAISE:
                    return  # No-op. Never raise in this case.
                elif on_dup_kv is IGNORE:
                    return
                # else on_dup_kv is OVERWRITE. Fall through to return on last line.
            else:
                # key and val each duplicate a different existing item.
                if on_dup_kv is RAISE:
                    raise KeyAndValueNotUniqueError(
                        (key, val), (inv[oldval], oldval), (oldkey, fwd[oldkey]))
                elif on_dup_kv is IGNORE:
                    return
                # else on_dup_kv is OVERWRITE. Fall through to return on last line.
        else:
            if isdupkey:
                if on_dup_key is RAISE:
                    raise KeyNotUniqueError((key, val), (inv[oldval], oldval))
                elif on_dup_key is IGNORE:
                    return
                # else on_dup_key is OVERWRITE. Fall through to return on last line.
            elif isdupval:
                if on_dup_val is RAISE:
                    raise ValueNotUniqueError((key, val), (oldkey, fwd[oldkey]))
                elif on_dup_val is IGNORE:
                    return
                # else on_dup_val is OVERWRITE. Fall through to return on last line.
            # else neither isdupkey nor isdupval (oldkey and oldval both _missing).
        return isdupkey, isdupval, oldkey, oldval

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
        if on_dup_kv is ON_DUP_VAL:
            on_dup_kv = on_dup_val
        failclean = not init or RAISE in (on_dup_key, on_dup_val, on_dup_kv)
        updated = self.copy() if failclean else self
        _put = updated._put
        for (k, v) in pairs(*args, **kw):
            _put(k, v, on_dup_key, on_dup_val, on_dup_kv)
        if failclean:
            self._become(updated)

    def _become(self, other):
        self._fwd = other._fwd
        self._inv = other._inv
        self.inv._fwd = self._inv
        self.inv._inv = self._fwd

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


class BidictException(Exception):
    """Base class for bidict exceptions."""


class UniquenessError(BidictException):
    """Base class for exceptions raised when uniqueness is violated."""


class KeyNotUniqueError(UniquenessError):
    """Raised when a given key is not unique."""

    def __str__(self):
        return ('%r duplicates key in item %r' % self.args) if self.args else ''


class ValueNotUniqueError(UniquenessError):
    """Raised when a given value is not unique."""

    def __str__(self):
        return ('%r duplicates value in item: %r' % self.args) if self.args else ''


class KeyAndValueNotUniqueError(KeyNotUniqueError, ValueNotUniqueError):
    """
    Raised when a given item's key and value are not unique.

    That is, its key duplicates that of another item,
    and its value duplicates that of a different other item.
    """

    def __str__(self):
        return ('%r duplicates key and value in items: %r, %r' % self.args) if self.args else ''

"""
Implements :class:`BidirectionalMapping`, the bidirectional map base class.

Also provides related exception classes and duplication behaviors.
"""

from .compat import PY2, iteritems
from .util import pairs, _arg0
from collections import Mapping, OrderedDict, Sized, deque


def _proxied(methodname, ivarname='_fwd', doc=None):
    """Make a func that calls methodname on the indicated instance variable."""
    def proxy(self, *args):
        ivar = getattr(self, ivarname)
        meth = getattr(ivar, methodname)
        return meth(*args)
    proxy.__name__ = methodname
    proxy.__doc__ = doc or 'Like :py:meth:`dict.%s`.' % methodname
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
    _precheck = True

    def __init__(self, *args, **kw):
        """Like :py:meth:`dict.__init__`, but maintaining bidirectionality."""
        self._fwd = self._dcls()  # dictionary of forward mappings
        self._inv = self._dcls()  # dictionary of inverse mappings
        if args or kw:
            self._update(self._on_dup_key, self._on_dup_val, self._on_dup_kv,
                         self._precheck, *args, **kw)
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

    def _put(self, key, val, on_dup_key, on_dup_val, on_dup_kv):
        result = self._dedup_item(key, val, on_dup_key, on_dup_val, on_dup_kv)
        if result:
            self._write_item(*result)

    def _dedup_item(self, key, val, on_dup_key, on_dup_val, on_dup_kv):
        """
        Check the given key and value for any duplication in self.

        Handle any duplication as per the given duplication behaviors.

        If duplication is found and the corresponding duplication behavior is
        *RAISE*, raise the appropriate error.

        If duplication is found and the corresponding duplication behavior is
        *IGNORE*, return *None*.

        If duplication is found and the corresponding duplication behavior is
        *OVERWRITE*, or if no duplication is found,
        return *(key, val), (oldkey, oldval)*.
        """
        _fwd = self._fwd
        _inv = self._inv
        oldv = _fwd.get(key, _missing)
        oldk = _inv.get(val, _missing)
        dupitem = oldv == val
        assert dupitem == (oldk == key)
        dupk = oldv is not _missing
        dupv = oldk is not _missing
        # Rather than pass `key` and `val` to the exceptions below, pass
        # `_inv[oldv]` and `_fwd[oldk]` so that existing values are given
        # exactly. Hash-equivalence != identity, e.g. hash(0) == hash(0.0)
        # but 0 is not 0.0.
        if dupk and dupv:
            if dupitem:  # (k, v) duplicates a previous item.
                if on_dup_kv is RAISE:
                    return  # Never want to raise in this case.
                elif on_dup_kv is IGNORE:
                    return
                # else on_dup_kv is OVERWRITE.
                # Fall through to the return on the last line.
            else:
                # k and v each duplicate a different previous item.
                if on_dup_kv is RAISE:
                    raise KeyAndValueExistError((_inv[oldv], oldv), (oldk, _fwd[oldk]))
                elif on_dup_kv is IGNORE:
                    return
                # else on_dup_kv is OVERWRITE.
        else:
            if dupk:
                if on_dup_key is RAISE:
                    raise KeyExistsError((_inv[oldv], oldv))
                elif on_dup_key is IGNORE:
                    return
                # else on_dup_key is OVERWRITE.
            elif dupv:
                if on_dup_val is RAISE:
                    raise ValueExistsError((oldk, _fwd[oldk]))
                elif on_dup_val is IGNORE:
                    return
                # else on_dup_val is OVERWRITE.
        return key, val, dupk, dupv, oldk, oldv

    def _write_item(self, key, val, dupk, dupv, oldk, oldv):
        # Only remove old key (val) before writing if we're not about to
        # write the same key (val). Thus if this is an orderedbidict, the
        # item is changed in place rather than moved to the end.
        if dupk and oldk != key:
            del self._fwd[self._inv.pop(oldv)]
        if dupv and oldv != val:
            # Use pop with defaults in case we just took the branch 2 lines up.
            self._inv.pop(self._fwd.pop(oldk, _missing), None)
        self._fwd[key] = val
        self._inv[val] = key

    def _update(self, on_dup_key, on_dup_val, on_dup_kv, precheck, *args, **kw):
        if not args and not kw:
            return
        _put = self._put
        if precheck:
            # Process dups within update.
            update = _dedup_update(on_dup_key, on_dup_val, on_dup_kv, *args, **kw)
            # Check if any dups between update and existing items in self would
            # cause an error. If so, raise it here, before applying the update.
            # Feeding into a 0-length deque consumes the generator without any
            # unnecessary accumulation.
            deque((self._dedup_item(k, v, on_dup_key, on_dup_val, on_dup_kv)
                   for (k, v) in pairs(update)), maxlen=0)
            update = pairs(update)
        else:
            update = pairs(*args, **kw)

        for (k, v) in update:
            _put(k, v, on_dup_key=on_dup_key, on_dup_val=on_dup_val, on_dup_kv=on_dup_kv)

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


def _dedup_update(on_dup_key, on_dup_val, on_dup_kv, *args, **kw):
    arg = _arg0(args) if args else None
    if isinstance(arg, Sized) and (len(arg) + len(kw) == 1):
        return arg or kw  # No need to dedup if only 1 item.
    if not kw and isinstance(arg, BidirectionalMapping):
        return arg  # No need to dedup if only a bidict arg.
    # Must dedup.
    updatefwd = OrderedDict()  # Order affects which items survive dedup.
    updateinv = {}
    for (k, v) in pairs(*args, **kw):
        pv = updatefwd.get(k, _missing)
        pk = updateinv.get(v, _missing)
        dupitem = pv == v
        assert dupitem == (pk == k)
        dupk = pv is not _missing
        dupv = pk is not _missing
        if dupk and dupv:
            if dupitem:  # (k, v) duplicates a previous item.
                if on_dup_kv is RAISE:
                    continue  # Never want to raise in this case.
                elif on_dup_kv is IGNORE:
                    continue
                # else on_dup_kv is OVERWRITE.
                # Fall through to the overwrite code below, so (k, v) comes
                # later in the update.
            else:
                # k and v each duplicate a different previous item.
                if on_dup_kv is RAISE:
                    raise KeyAndValueNotUniqueError((k, v))
                elif on_dup_kv is IGNORE:
                    continue
                # else on_dup_kv is OVERWRITE.
        else:
            if dupk:
                if on_dup_key is RAISE:
                    raise KeyNotUniqueError(k)
                elif on_dup_key is IGNORE:
                    continue
                # else on_dup_key is OVERWRITE.
            elif dupv:
                if on_dup_val is RAISE:
                    raise ValueNotUniqueError(v)
                elif on_dup_val is IGNORE:
                    continue
                # else on_dup_val is OVERWRITE.
        # Popping any items we're about to overwrite first ensures that
        # the overwriting items come later, preserving relative ordering
        # within the update.
        if dupk:
            del updatefwd[updateinv.pop(pv)]
        if dupv:
            # Use pop with defaults in case we just took the branch 2 lines up.
            updateinv.pop(updatefwd.pop(pk, _missing), None)
        updatefwd[k] = v
        updateinv[v] = k
    return updatefwd


class BidictException(Exception):
    """Base class for bidict exceptions."""


class UniquenessError(BidictException):
    """Base class for exceptions raised when uniqueness is violated."""


class KeyNotUniqueError(UniquenessError):
    """Raised when a given key is not unique."""


class ValueNotUniqueError(UniquenessError):
    """Raised when a given value is not unique."""


class KeyAndValueNotUniqueError(KeyNotUniqueError, ValueNotUniqueError):
    """
    Raised when a given item's key and value are not unique.

    That is, its key duplicates that of another item,
    and its value duplicates that of a different other item.
    """


class KeyExistsError(KeyNotUniqueError):
    """
    Raised when attempting to insert an item
    whose key duplicates that of an already-existing item.
    """

    def __str__(self):
        return 'Key {0!r} exists with value {1!r}'.format(*self.args[0]) if self.args else ''


class ValueExistsError(ValueNotUniqueError):
    """
    Raised when attempting to insert an item
    whose value duplicates that of an already-existing item.
    """

    def __str__(self):
        return 'Value {1!r} exists with key {0!r}'.format(*self.args[0]) if self.args else ''


class KeyAndValueExistError(KeyExistsError, ValueExistsError, KeyAndValueNotUniqueError):
    """
    Raised when attempting to insert an item
    whose key duplicates that of an already-existing item,
    and whose value duplicates that of a different already-existing item.
    """

    def __str__(self):
        return ('Key {0[0]!r} exists with value {0[1]!r}, and value {1[1]!r} '
                'exists with key {1[0]!r}'.format(*self.args) if self.args else '')

"""
Implements :class:`BidirectionalMapping`, the bidirectional map base class.

Also provides related exception classes and duplication behaviors.
"""

from .compat import PY2, iteritems
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
        return '<%s>' % self.id

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

    def __init__(self, *args, **kw):
        """Like :py:meth:`dict.__init__`, but maintaining bidirectionality."""
        self._fwd = self._dcls()  # dictionary of forward mappings
        self._inv = self._dcls()  # dictionary of inverse mappings
        if args or kw:
            self._update(self._on_dup_key, self._on_dup_val, True, *args, **kw)
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

    def _dedup1(self, key, val, on_dup_key, on_dup_val):
        _fwd = self._fwd
        _inv = self._inv
        oldv = _fwd.get(key, _missing)
        dupk = oldv is not _missing
        if oldv == val or (dupk and on_dup_key is IGNORE):
            return
        if dupk and on_dup_key is RAISE:
            raise KeyExistsError((_inv[oldv], oldv))
        oldk = _inv.get(val, _missing)
        dupv = oldk is not _missing
        if oldk == key or (dupv and on_dup_val is IGNORE):
            return
        if dupv and on_dup_val is RAISE:
            raise ValueExistsError((oldk, _fwd[oldk]))
        return (key, val), (oldk, oldv)

    def _put(self, key, val, on_dup_key, on_dup_val):
        # Could just call _update(on_dup_key, on_dup_val, False, ((key, val),))
        # but special-casing single-item update is faster.
        result = self._dedup1(key, val, on_dup_key, on_dup_val)
        if result:
            (key, val), (oldk, oldv) = result
            self._fwd.pop(oldk, None)
            self._inv.pop(oldv, None)
            self._fwd[key] = val
            self._inv[val] = key

    def _update(self, on_dup_key, on_dup_val, atomic, *args, **kw):
        if not args and not kw:
            return
        arg = args[0] if args else {}
        argsized = hasattr(arg, '__len__')
        arglen = argsized and len(arg)
        if argsized and not arglen and not kw:
            return
        update_len_1 = argsized and (arglen + len(kw) == 1)
        only_bimap_arg = isinstance(arg, BidirectionalMapping) and not kw
        overwrite_kv = on_dup_key is OVERWRITE and on_dup_val is OVERWRITE
        skip_dedup_update = update_len_1 or only_bimap_arg or overwrite_kv
        update = pairs(arg, **kw) if skip_dedup_update else (
                     _dedup_in(self._dcls, on_dup_key, on_dup_val, arg, **kw))
        _fwd = self._fwd
        if _fwd:  # Must process dups between self (existing items) and update.
            update = self._dedup(on_dup_key, on_dup_val, update)
        if atomic:  # Must realize update before applying.
            update = tuple(update)  # Any exceptions raised here, early.
        _inv = self._inv
        _fwdpop = _fwd.pop
        _invpop = _inv.pop
        for (k, v) in update:  # Finally, apply the update.
            _invpop(_fwdpop(k, _missing), None)
            _fwdpop(_invpop(v, _missing), None)
            _fwd[k] = v
            _inv[v] = k

    def _dedup(self, on_dup_key, on_dup_val, update):
        """
        Yield items in *update*, deduplicating with items already in self.

        If an item in *update* duplicates only an existing key in self, the
        item is ignored or an exception is raised if *on_dup_key* is *IGNORE*
        or *RAISE*, respectively.

        If an item in *update* duplicates only an existing value in self, the
        item is ignored or an exception is raised if *on_dup_val* is *IGNORE*
        or *RAISE*, respectively.

        If an item in *update* is already in self, it is ignored no matter what
        *on_dup_key* and *on_dup_val* are set to.
        """
        for (k, v) in update:
            result = self._dedup1(k, v, on_dup_key, on_dup_val)
            if result:
                yield result[0]

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


def _dedup_in(dcls, on_dup_key, on_dup_val, arg, **kw):
    """
    Yield items in *arg* and *kw*, deduplicating any duplicates within them.

    Items in *arg* and *kw* that have duplicate keys or values will be ignored
    or will cause an exception, as per the given duplication behaviors.
    """
    argmap = None
    on_dup_key_raise = on_dup_key is RAISE
    on_dup_val_raise = on_dup_val is RAISE
    on_dup_key_ignore = on_dup_key is IGNORE
    on_dup_val_ignore = on_dup_val is IGNORE
    if arg:
        if isinstance(arg, BidirectionalMapping):
            argmap = arg
            arginv = arg.inv
            for (k, v) in iteritems(arg):
                yield (k, v)
        else:
            argismap = isinstance(arg, Mapping)
            if argismap:
                it = iteritems(arg)
                argmap = arg
            else:
                it = iter(arg)
                argmap = dcls()
            arginv = dcls()
            for (k, v) in it:
                if not argismap:
                    pv = argmap.get(k, _missing)
                    if pv == v:
                        continue
                    if pv is not _missing:
                        if on_dup_key_raise:
                            raise KeyNotUniqueError(k)
                        if on_dup_key_ignore:
                            continue
                    argmap[k] = v
                pk = arginv.get(v, _missing)
                if pk == k:
                    continue
                if pk is not _missing:
                    if on_dup_val_raise:
                        raise ValueNotUniqueError(v)
                    if on_dup_val_ignore:
                        continue
                arginv[v] = k
                yield (k, v)
    if kw:
        kwinv = dcls()
        for (k, v) in iteritems(kw):
            if argmap:
                argv = argmap.get(k, _missing)
                if argv == v:
                    continue
                elif argv is not _missing:
                    if on_dup_key_raise:
                        raise KeyNotUniqueError(k)
                    if on_dup_key_ignore:
                        continue
                argk = arginv.get(v, _missing)
                if argk == k:
                    continue
                elif argk is not _missing:
                    if on_dup_val_raise:
                        raise ValueNotUniqueError(v)
                    if on_dup_val_ignore:
                        continue
            pk = kwinv.get(v, _missing)
            if pk == k:
                continue
            if pk is not _missing:
                if on_dup_val_raise:
                    raise ValueNotUniqueError(v)
                if on_dup_val_ignore:
                    continue
            kwinv[k] = v
            yield (k, v)


class BidictException(Exception):
    """Base class for bidict exceptions."""


class UniquenessError(BidictException):
    """Base class for exceptions raised when uniqueness is violated."""


class KeyNotUniqueError(UniquenessError):
    """Raised when a given key is not unique."""


class ValueNotUniqueError(UniquenessError):
    """Raised when a given value is not unique."""


class KeyExistsError(KeyNotUniqueError):
    """Raised when attempting to insert an already-existing key."""

    def __str__(self):
        if self.args:
            return 'Key {0!r} exists with value {1!r}'.format(*self.args[0])
        return ''


class ValueExistsError(ValueNotUniqueError):
    """Raised when attempting to insert an already-existing value."""

    def __str__(self):
        if self.args:
            return 'Value {1!r} exists with key {0!r}'.format(*self.args[0])
        return ''

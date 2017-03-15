"""Provides various common functionality."""

from .compat import PY2, iteritems
from .util import pairs
from abc import abstractproperty
from collections import ItemsView, Mapping


class BidirectionalMapping(Mapping):
    """Abstract base class for bidirectional mappings.
    Extends :class:`collections.abc.Mapping`.

    .. py:attribute:: _subclsattrs

        The attributes that :attr:`__subclasshook__` checks for to determine
        whether a class is a subclass of :class:`BidirectionalMapping`.

    """

    __slots__ = ()

    @abstractproperty
    def inv(self):
        """The inverse bidict."""
        raise NotImplementedError  # pragma: no cover

    def __inverted__(self):
        """Get an iterator over the items in :attr:`inv`."""
        return iteritems(self.inv)

    _subclsattrs = frozenset({
        'inv', '__inverted__',
        # see "Mapping" in the table at
        # https://docs.python.org/3/library/collections.abc.html#collections-abstract-base-classes
        '__getitem__', '__iter__', '__len__',  # abstract methods
        '__contains__', 'keys', 'items', 'values', 'get', '__eq__', '__ne__',  # mixin methods
    })

    @classmethod
    def __subclasshook__(cls, C):
        """Check if C provides all the attributes in :attr:`_subclsattrs`.

        Causes conforming classes to be virtual subclasses automatically.
        """
        mro = getattr(C, '__mro__', None)
        if mro and cls is BidirectionalMapping:
            return all(any(B.__dict__.get(i) for B in mro) for i in cls._subclsattrs)
        return NotImplemented


class _marker(object):
    def __init__(self, id):
        self.id = id

    def __repr__(self):
        return '<%s>' % self.id  # pragma: no cover


class DuplicationBehavior(_marker):
    """
    Provide RAISE, OVERWRITE, IGNORE, and ON_DUP_VAL duplication behaviors.

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


def _proxied(methodname, attrname='_fwd', doc=None):
    """Make a func that calls the indicated method on the indicated attribute."""
    def proxy(self, *args):
        attr = getattr(self, attrname)
        meth = getattr(attr, methodname)
        return meth(*args)
    proxy.__name__ = methodname
    proxy.__doc__ = doc or "Like dict's ``%s``." % methodname
    return proxy


class BidictBase(BidirectionalMapping):
    """
    Base class for all provided bidirectional map types.

    Mutable and immutable bidict types extend this class,
    which implements all the shared logic.
    Users will typically only interact with subclasses of this class.

    .. py:attribute:: _fwd

        The backing one-way dict for the forward items.

    .. py:attribute:: _inv

        The backing one-way dict for inverse items.

    .. py:attribute:: _fwd_class

        The Mapping type used for the backing _fwd dict.

    .. py:attribute:: _inv_class

        The Mapping type used for the backing _inv dict.

    .. py:attribute:: _isinv

        :class:`bool` representing whether this bidict is the inverse of some
        other bidict which has already been created. If True, the meaning of
        :attr:`_fwd_class` and :attr:`_inv_class` is swapped. This enables
        the inverse of a bidict specifying a different :attr:`_fwd_class` and
        :attr:`_inv_class` to be passed back into its constructor such that
        the resulting copy has its :attr:`_fwd_class` and :attr:`_inv_class`
        set correctly.

    .. py:attribute:: _on_dup_key

        :class:`DuplicationBehavior` in the event of a key duplication.

    .. py:attribute:: _on_dup_val

        :class:`DuplicationBehavior` in the event of a value duplication.

    .. py:attribute:: _on_dup_kv

        :class:`DuplicationBehavior` in the event of key and value duplication.

    """

    _on_dup_key = OVERWRITE
    _on_dup_val = RAISE
    _on_dup_kv = RAISE
    _fwd_class = dict
    _inv_class = dict

    def __init__(self, *args, **kw):
        """Like dict's ``__init__``."""
        self._isinv = getattr(args[0], '_isinv', False) if args else False
        self._fwd = self._inv_class() if self._isinv else self._fwd_class()
        self._inv = self._fwd_class() if self._isinv else self._inv_class()
        self._init_inv()
        if args or kw:
            self._update(True, self._on_dup_key, self._on_dup_val, self._on_dup_kv, *args, **kw)

    def _init_inv(self):
        inv = object.__new__(self.__class__)
        inv._isinv = not self._isinv
        inv._fwd_class = self._inv_class
        inv._inv_class = self._fwd_class
        inv._fwd = self._inv
        inv._inv = self._fwd
        inv.__inv = self
        self.__inv = inv

    @property
    def inv(self):
        """The inverse bidict."""
        return self.__inv

    def __repr__(self):
        s = self.__class__.__name__ + '('
        if not self:
            return s + ')'
        # If we have a truthy __reversed__ attribute, use an ordered repr.
        # (Python doesn't provide an Ordered or OrderedMapping ABC, else we'd
        # use that. Must use getattr rather than hasattr since __reversed__
        # may be set to None, which signifies non-ordered/-reversible.)
        if getattr(self, '__reversed__', None):
            return s + '[' + ', '.join(repr(i) for i in iteritems(self)) + '])'
        return s + '{' + ', '.join('%r: %r' % i for i in iteritems(self)) + '})'

    def __eq__(self, other):
        # This should be faster than using Mapping.__eq__'s implementation.
        return self._fwd == other

    def _pop(self, key):
        val = self._fwd.pop(key)
        del self._inv[val]
        return val

    def _clear(self):
        self._fwd.clear()
        self._inv.clear()

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
        *(isdupkey, isdupval, invbyval, fwdbykey)*.
        """
        fwd = self._fwd
        inv = self._inv
        fwdbykey = fwd.get(key, _missing)
        invbyval = inv.get(val, _missing)
        isdupkey = fwdbykey is not _missing
        isdupval = invbyval is not _missing
        if isdupkey and isdupval:
            if self._isdupitem(key, val, invbyval, fwdbykey):
                # (key, val) duplicates an existing item -> no-op.
                return
            # key and val each duplicate a different existing item.
            if on_dup_kv is RAISE:
                raise KeyAndValueDuplicationError(key, val)
            elif on_dup_kv is IGNORE:
                return
            # else on_dup_kv is OVERWRITE. Fall through to return on last line.
        elif isdupkey:
            if on_dup_key is RAISE:
                raise KeyDuplicationError(key)
            elif on_dup_key is IGNORE:
                return
            # else on_dup_key is OVERWRITE. Fall through to return on last line.
        elif isdupval:
            if on_dup_val is RAISE:
                raise ValueDuplicationError(val)
            elif on_dup_val is IGNORE:
                return
            # else on_dup_val is OVERWRITE. Fall through to return on last line.
        # else neither isdupkey nor isdupval.
        return isdupkey, isdupval, invbyval, fwdbykey

    def _isdupitem(self, key, val, oldkey, oldval):
        dup = oldkey == key
        assert dup == (oldval == val)
        return dup

    def _write_item(self, key, val, isdupkey, isdupval, oldkey, oldval):
        self._fwd[key] = val
        self._inv[val] = key
        if isdupkey:
            del self._inv[oldval]
        if isdupval:
            del self._fwd[oldkey]
        return key, val, isdupkey, isdupval, oldkey, oldval

    def _update(self, init, on_dup_key, on_dup_val, on_dup_kv, *args, **kw):
        if not args and not kw:
            return
        if on_dup_kv is ON_DUP_VAL:
            on_dup_kv = on_dup_val
        rollbackonfail = not init or RAISE in (on_dup_key, on_dup_val, on_dup_kv)
        if rollbackonfail:
            return self._update_rbf(on_dup_key, on_dup_val, on_dup_kv, *args, **kw)
        _put = self._put
        for (key, val) in pairs(*args, **kw):
            _put(key, val, on_dup_key, on_dup_val, on_dup_kv)

    def _update_rbf(self, on_dup_key, on_dup_val, on_dup_kv, *args, **kw):
        """Update, rolling back on failure."""
        exc = None
        writes = []
        appendwrite = writes.append
        dedup_item = self._dedup_item
        write_item = self._write_item
        for (key, val) in pairs(*args, **kw):
            try:
                dedup_result = dedup_item(key, val, on_dup_key, on_dup_val, on_dup_kv)
            except DuplicationError as e:
                exc = e
                break
            if dedup_result:
                write_result = write_item(key, val, *dedup_result)
                appendwrite(write_result)
        if exc:
            undo_write = self._undo_write
            for write in reversed(writes):
                undo_write(*write)
            raise exc

    def _undo_write(self, key, val, isdupkey, isdupval, oldkey, oldval):
        fwd = self._fwd
        inv = self._inv
        if not isdupkey and not isdupval:
            self._pop(key)
            return
        if isdupkey:
            fwd[key] = oldval
            inv[oldval] = key
            if not isdupval:
                del inv[val]
        if isdupval:
            inv[val] = oldkey
            fwd[oldkey] = val
            if not isdupkey:
                del fwd[key]

    def copy(self):
        """Like :py:meth:`dict.copy`."""
        # This should be faster than ``return self.__class__(self)`` because
        # it avoids the unnecessary duplicate checking.
        copy = object.__new__(self.__class__)
        copy._isinv = self._isinv
        copy._fwd = self._fwd.copy()
        copy._inv = self._inv.copy()
        cinv = object.__new__(self.__class__)
        cinv._isinv = not self._isinv
        cinv._fwd_class = self._inv_class
        cinv._inv_class = self._fwd_class
        cinv._fwd = copy._inv
        cinv._inv = copy._fwd
        cinv.__inv = copy
        copy.__inv = cinv
        return copy

    __copy__ = copy
    __len__ = _proxied('__len__')
    __iter__ = _proxied('__iter__')
    __getitem__ = _proxied('__getitem__')
    values = _proxied('keys', attrname='inv')
    values.__doc__ = \
        "B.values() -> a set-like object providing a view on B's values.\n\n" \
        'Note that because values of a BidirectionalMapping are also keys\n' \
        'of its inverse, this returns a *KeysView* object rather than a\n' \
        '*ValuesView* object, conferring set-like benefits.'
    if PY2:  # pragma: no cover
        viewkeys = _proxied('viewkeys')

        viewvalues = _proxied('viewkeys', attrname='inv',
                              doc=values.__doc__.replace('values()', 'viewvalues()'))
        values.__doc__ = "Like dict's ``values``."

        # Use ItemsView here rather than proxying to _fwd.viewitems() so that
        # OrderedBidictBase (whose _fwd's values are nodes, not bare values)
        # can use it.
        viewitems = lambda self: ItemsView(self)


class BidictException(Exception):
    """Base class for bidict exceptions."""


class DuplicationError(BidictException):
    """Base class for exceptions raised when uniqueness is violated."""


class KeyDuplicationError(DuplicationError):
    """Raised when a given key is not unique."""


class ValueDuplicationError(DuplicationError):
    """Raised when a given value is not unique."""


class KeyAndValueDuplicationError(KeyDuplicationError, ValueDuplicationError):
    """
    Raised when a given item's key and value are not unique.

    That is, its key duplicates that of another item,
    and its value duplicates that of a different other item.
    """

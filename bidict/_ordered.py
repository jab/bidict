"""Implements :class:`bidict.orderedbidict` and friends."""

from ._bidict import bidict
from ._common import BidictBase, _marker, _missing
from .compat import iteritems, izip
from collections import Mapping


_PRV = 1
_NXT = 2
_END = _marker('END')


def _make_iter(reverse=False, name='__iter__', doc=None):
    def _iter(self):
        fwd = self._fwd
        end = self._end
        cur = end[_PRV if reverse else _NXT]
        while cur is not end:
            d, prv, nxt = cur
            korv = next(iter(d))
            node = fwd.get(korv)
            yield korv if node is cur else d[korv]
            cur = prv if reverse else nxt
    _iter.__name__ = name
    _iter.__doc__ = doc or "Like OrderedDict's ``%s``." % name
    return _iter


class OrderedBidictBase(BidictBase):
    """Base class for :class:`orderedbidict` and :class:`frozenorderedbidict`."""

    def __init__(self, *args, **kw):  # noqa: D102
        self._isinv = getattr(args[0], '_isinv', False) if args else False
        self._end = []  # circular doubly-linked list of [{key: val, val: key}, prv, nxt] nodes
        self._init_end()
        self._fwd = {}  # key -> node. _fwd_class ignored.
        self._inv = {}  # val -> node. _inv_class ignored.
        self._init_inv()
        if args or kw:
            self._update(True, self._on_dup_key, self._on_dup_val, self._on_dup_kv, *args, **kw)

    def _init_end(self):
        end = self._end
        end += [_END, end, end]  # sentinel node for doubly linked list

    def _init_inv(self):
        super(OrderedBidictBase, self)._init_inv()
        self.inv._end = self._end

    # Must override BidictBase.copy since we have different internal structure.
    def copy(self):
        """Like :attr:`BidictBase.copy <bidict.BidictBase.copy>`."""
        return self.__class__(self)

    __copy__ = copy

    def _clear(self):
        super(OrderedBidictBase, self)._clear()
        del self._end[:]
        self._init_end()

    def __getitem__(self, key):
        node = self._fwd[key]
        d = node[0]
        return d[key]

    def _pop(self, key):
        nodefwd = self._fwd.pop(key)
        d, prv, nxt = nodefwd
        val = d[key]
        nodeinv = self._inv.pop(val)
        assert nodeinv is nodefwd
        prv[_NXT] = nxt
        nxt[_PRV] = prv
        del nodefwd[:]
        return val

    def _isdupitem(self, key, val, nodeinv, nodefwd):
        """Return whether (key, val) duplicates an existing item."""
        return nodeinv is nodefwd

    def _write_item(self, key, val, isdupkey, isdupval, nodeinv, nodefwd):
        fwd = self._fwd
        inv = self._inv
        if not isdupkey and not isdupval:
            end = self._end
            lst = end[_PRV]
            node = [{key: val, val: key}, lst, end]
            end[_PRV] = lst[_NXT] = fwd[key] = inv[val] = node
            oldkey = oldval = _missing
        elif isdupkey and isdupval:
            fwdd, fwdprv, fwdnxt = nodefwd
            oldval = fwdd[key]
            invd, invprv, invnxt = nodeinv
            oldkey = invd[val]
            assert oldkey != key
            assert oldval != val
            # We have to collapse nodefwd and nodeinv into a single node.
            # Drop nodeinv so that item with same key overwritten in place.
            invprv[_NXT] = invnxt
            invnxt[_PRV] = invprv
            # Don't remove nodeinv's references to its neighbors since
            # if the update fails, we'll need them to undo this write.
            # Python's garbage collector should still be able to detect when
            # nodeinv is garbage and reclaim the memory.
            # Update fwd and inv.
            assert fwd.pop(oldkey) is nodeinv
            assert inv.pop(oldval) is nodefwd
            fwd[key] = inv[val] = nodefwd
            # Update nodefwd with new item.
            fwdd.clear()
            fwdd[key] = val
            fwdd[val] = key
        elif isdupkey:
            d = nodefwd[0]
            oldval = d[key]
            oldkey = _missing
            oldnodeinv = inv.pop(oldval)
            assert oldnodeinv is nodefwd
            inv[val] = nodefwd
        elif isdupval:
            d = nodeinv[0]
            oldkey = d[val]
            oldval = _missing
            oldnodefwd = fwd.pop(oldkey)
            assert oldnodefwd is nodeinv
            fwd[key] = nodeinv
        if isdupkey ^ isdupval:
            d.clear()
            d[key] = val
            d[val] = key
        return key, val, isdupkey, isdupval, nodeinv, nodefwd, oldkey, oldval

    def _undo_write(self, key, val, isdupkey, isdupval, nodeinv, nodefwd, oldkey, oldval):
        fwd = self._fwd
        inv = self._inv
        if not isdupkey and not isdupval:
            del self[key]
        elif isdupkey and isdupval:
            fwdd, fwdprv, fwdnxt = nodefwd
            invd, invprv, invnxt = nodeinv
            # Restore original items.
            fwdd.clear()
            fwdd[key] = oldval
            fwdd[oldval] = key
            # invd was never changed so should still have the original item.
            expectinvd = {oldkey: val, val: oldkey}
            assert invd == expectinvd
            # Undo replacing nodeinv with nodefwd.
            invprv[_NXT] = invnxt[_PRV] = nodeinv
            fwd[oldkey] = inv[val] = nodeinv
            inv[oldval] = fwd[key] = nodefwd
        elif isdupkey:
            d = nodefwd[0]
            d.clear()
            d[key] = oldval
            d[oldval] = key
            assert inv.pop(val) is nodefwd
            inv[oldval] = nodefwd
            assert fwd[key] is nodefwd
        elif isdupval:
            d = nodeinv[0]
            d.clear()
            d[oldkey] = val
            d[val] = oldkey
            assert fwd.pop(key) is nodeinv
            fwd[oldkey] = nodeinv
            assert inv[val] is nodeinv

    __iter__ = _make_iter()
    __reversed__ = _make_iter(reverse=True, name='__reversed__')

    def __eq__(self, other):
        if not isinstance(other, Mapping):
            return NotImplemented
        if len(self) != len(other):
            return False
        if self._should_compare_order_sensitive(other):
            return all(i == j for (i, j) in izip(iteritems(self), iteritems(other)))
        return all(self.get(k, _missing) == v for (k, v) in iteritems(other))

    def _should_compare_order_sensitive(self, mapping):
        """Whether we should compare order-sensitively to ``mapping``.

        Returns True iff ``isinstance(mapping, OrderedBidictBase)``.
        Override this in a subclass to customize this behavior.
        """
        return isinstance(mapping, OrderedBidictBase)


class orderedbidict(OrderedBidictBase, bidict):
    """Mutable bidict type that maintains items in insertion order."""

    def popitem(self, last=True):
        """Like :meth:`collections.OrderedDict.popitem`."""
        if not self:
            raise KeyError(self.__class__.__name__ + ' is empty')
        key = next((reversed if last else iter)(self))
        val = self._pop(key)
        return key, val

    def move_to_end(self, key, last=True):
        """Like :meth:`collections.OrderedDict.move_to_end`."""
        node = self._fwd[key]
        d, prv, nxt = node
        prv[_NXT] = nxt
        nxt[_PRV] = prv
        end = self._end
        if last:
            lst = end[_PRV]
            node[_PRV] = lst
            node[_NXT] = end
            end[_PRV] = lst[_NXT] = node
        else:
            fst = end[_NXT]
            node[_PRV] = end
            node[_NXT] = fst
            end[_NXT] = fst[_PRV] = node

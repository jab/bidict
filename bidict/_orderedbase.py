# -*- coding: utf-8 -*-
# Copyright 2018 Joshua Bronson. All Rights Reserved.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


#==============================================================================
#                    * Welcome to the bidict source code *
#==============================================================================

# Doing a code review? You'll find a "Code review nav" comment like the one
# below at the top and bottom of the most important source files. This provides
# a suggested initial path through the source when reviewing.
#
# Note: If you aren't reading this on https://github.com/jab/bidict, you may be
# viewing an outdated version of the code. Please head to GitHub to review the
# latest version, which contains important improvements over older versions.
#
# Thank you for reading and for any feedback you provide.

#                             * Code review nav *
#==============================================================================
#  ← Prev: _bidict.py       Current: _orderedbase.py  Next: _frozenordered.py →
#==============================================================================


"""Provides :class:`OrderedBidictBase`."""

from weakref import ref

from ._base import _WriteResult, BidictBase
from ._miss import _MISS
from .compat import KeysView, ItemsView, Mapping, PY2, iteritems, izip


class _Node(object):  # pylint: disable=too-few-public-methods
    """A node in a circular doubly-linked list
    that stores the items in an ordered bidict.

    Only weak references to the next and previous nodes
    are held to avoid creating strong reference cycles.

    Because an ordered bidict retains two strong references
    to each node instance (one from its backing `_fwdm` dict
    and one from its `_invm` dict), a node's refcount will not
    drop to zero (and so will not be garbage collected) as long as
    the ordered bidict that contains it is still alive.
    Because nodes don't have strong reference cycles,
    once their containing bidict is freed, they can be freed too.
    """

    __slots__ = ('_korv', '_vork', '_prv', '_nxt', '__weakref__')

    def __init__(self, korv, vork, prv=None, nxt=None):
        self._korv = korv
        self._vork = vork
        self._setprv(prv)
        self._setnxt(nxt)

    def _getdata(self):
        return (self._korv, self._vork)

    def _setdata(self, data):
        self._korv, self._vork = data

    data = property(_getdata, _setdata)

    def __repr__(self):
        clsname = self.__class__.__name__
        prv = self.prv and self.prv.data
        nxt = self.nxt and self.nxt.data
        return '%s(prv=%s, data=%s, nxt=%s)' % (clsname, prv, self.data, nxt)

    def _getprv(self):
        return self._prv() if isinstance(self._prv, ref) else self._prv

    def _setprv(self, prv):
        self._prv = prv and ref(prv)

    prv = property(_getprv, _setprv)

    def _getnxt(self):
        return self._nxt() if isinstance(self._nxt, ref) else self._nxt

    def _setnxt(self, nxt):
        self._nxt = nxt and ref(nxt)

    nxt = property(_getnxt, _setnxt)

    def __getitem__(self, key_or_val):
        """Node items are stored as (key, value) pairs
        from the perspective of the forward mapping,
        and (value, key) pairs from the perspective of the inverse.

        This method provides a convenient way
        to get the key of a node if you know its value
        or the value of a node if you know its key.

        :raises KeyError: if *key_or_val* is neither this node's key nor value.

        >>> node = _Node('key', 'val')
        >>> node['key']
        'val'
        >>> node['val']
        'key'
        >>> node['missing']
        Traceback (most recent call last):
            ...
        KeyError: 'missing'
        """
        korv = self._korv
        vork = self._vork
        if key_or_val == korv:
            return vork
        elif key_or_val == vork:
            return korv
        raise KeyError(key_or_val)

    def __getstate__(self):
        """Return the instance state dictionary
        but with weakrefs converted to strong refs
        so that it can be pickled.

        *See also* :meth:`object.__getstate__`
        """
        return dict(_korv=self._korv, _vork=self._vork, _prv=self.prv, _nxt=self.nxt)

    def __setstate__(self, state):
        """Set the instance state from *state*."""
        self._korv = state['_korv']
        self._vork = state['_vork']
        self._setprv(state['_prv'])
        self._setnxt(state['_nxt'])


class _Sentinel(_Node):  # pylint: disable=too-few-public-methods
    """Special node in a circular doubly-linked list
    that links the first node with the last node.
    When its next and previous references point back to itself
    it represents an empty list.
    """

    __slots__ = ()

    def __init__(self, prv=None, nxt=None):
        super(_Sentinel, self).__init__(_MISS, _MISS, prv or self, nxt or self)

    def __repr__(self):
        return '<SENTINEL>'

    def __bool__(self):  # Useful for _Node.__repr__ (see above).
        return False

    if PY2:
        __nonzero__ = __bool__


def _iter_nodes(sntl, reverse=False):
    """Given the sentinel node of a circular doubly-linked list,
    iterate over the remaining nodes in the order specified by *reverse*.

    >>> sntl = _Sentinel()
    >>> node = _Node('key', 'val', sntl, sntl)
    >>> sntl.nxt = sntl.prv = node
    >>> list(_iter_nodes(sntl))
    [_Node(prv=<SENTINEL>, data=('key', 'val'), nxt=<SENTINEL>)]
    """
    attr = 'prv' if reverse else 'nxt'
    node = getattr(sntl, attr)
    while node is not sntl:  # lgtm [py/comparison-using-is]
        yield node
        node = getattr(node, attr)


class OrderedBidictBase(BidictBase):  # lgtm [py/missing-equals]
    """Base class implementing an ordered :class:`BidirectionalMapping`."""

    __slots__ = ('_sntl',)

    def __init__(self, *args, **kw):
        """Make a new ordered bidirectional mapping.
        The signature is the same as that of regular dictionaries.
        Items passed in are added in the order they are passed,
        respecting this bidict type's duplication policies along the way.
        The order in which items are inserted is remembered,
        similar to :class:`collections.OrderedDict`.
        """
        self._sntl = _Sentinel()

        # Like unordered bidicts, ordered bidicts also store two backing one-directional mappings
        # `_fwdm` and `_invm`. But rather than mapping `key` to `val` and `val` to `key`
        # (respectively), they map `key` to `nodefwd` and `val` to `nodeinv` (respectively), where
        # `nodefwd` is `nodeinv` when `key` and `val` are associated with one another.

        # To effect this difference, `_write_item` and `_undo_write` are overridden. But much of the
        # rest of BidictBase's implementation, including BidictBase.__init__ and BidictBase._update,
        # are inherited and are able to be reused without modification.
        super(OrderedBidictBase, self).__init__(*args, **kw)

    def _init_inv(self):
        super(OrderedBidictBase, self)._init_inv()
        self.inv._sntl = self._sntl  # pylint: disable=protected-access

    # Can't reuse BidictBase.copy since ordered bidicts have different internal structure.
    def copy(self):
        """A shallow copy of this ordered bidict."""
        # Fast copy implementation bypassing __init__. See comments in :meth:`BidictBase.copy`.
        copy = self.__class__.__new__(self.__class__)
        sntl = _Sentinel()
        fwdm = dict.fromkeys(self._fwdm)
        invm = dict.fromkeys(self._invm)
        cur = sntl
        nxt = sntl.nxt
        for (key, val) in iteritems(self):
            nxt = _Node(key, val, cur, sntl)
            cur.nxt = fwdm[key] = invm[val] = nxt
            cur = nxt
        sntl.prv = nxt
        copy._sntl = sntl  # pylint: disable=protected-access
        copy._fwdm = fwdm  # pylint: disable=protected-access
        copy._invm = invm  # pylint: disable=protected-access
        copy._init_inv()  # pylint: disable=protected-access
        return copy

    def __getitem__(self, key):
        nodefwd = self._fwdm[key]
        val = nodefwd[key]
        nodeinv = self._invm[val]
        assert nodeinv is nodefwd
        return val

    def _pop(self, key):
        nodefwd = self._fwdm.pop(key)
        val = nodefwd[key]
        nodeinv = self._invm.pop(val)
        assert nodeinv is nodefwd
        nodefwd.prv.nxt = nodefwd.nxt
        nodefwd.nxt.prv = nodefwd.prv
        return val

    def _isdupitem(self, key, val, dedup_result):
        """Return whether (key, val) duplicates an existing item."""
        isdupkey, isdupval, nodeinv, nodefwd = dedup_result
        isdupitem = nodeinv is nodefwd
        if isdupitem:
            assert isdupkey
            assert isdupval
            assert nodefwd[key] == val
            assert nodefwd[val] == key
        return isdupitem

    def _write_item(self, key, val, dedup_result):  # pylint: disable=too-many-locals
        fwdm = self._fwdm
        invm = self._invm
        # Order of (key, val) in node data is not significant but might as well try to keep uniform.
        nodedata = (val, key) if self._isinv else (key, val)
        isdupkey, isdupval, nodeinv, nodefwd = dedup_result
        if not isdupkey and not isdupval:
            # No key or value duplication -> create and append a new node.
            sntl = self._sntl
            last = sntl.prv
            node = _Node(nodedata[0], nodedata[1], last, sntl)
            last.nxt = sntl.prv = fwdm[key] = invm[val] = node
            oldkey = oldval = _MISS
        elif isdupkey and isdupval:
            # Key and value duplication across two different nodes.
            assert nodefwd is not nodeinv
            oldval = nodefwd[key]
            oldkey = nodeinv[val]
            assert oldkey != key
            assert oldval != val
            # We have to collapse nodefwd and nodeinv into a single node, i.e. drop one of them.
            # Drop nodeinv, so that the item with the same key is the one overwritten in place.
            nodeinv.prv.nxt = nodeinv.nxt
            nodeinv.nxt.prv = nodeinv.prv
            # Don't remove nodeinv's references to its neighbors since
            # if the update fails, we'll need them to undo this write.
            # Update fwdm and invm.
            tmp = fwdm.pop(oldkey)
            assert tmp is nodeinv
            tmp = invm.pop(oldval)
            assert tmp is nodefwd
            fwdm[key] = invm[val] = nodefwd
            # Update nodefwd with new item.
            nodefwd.data = nodedata
        elif isdupkey:
            oldval = nodefwd[key]
            oldkey = _MISS
            oldnodeinv = invm.pop(oldval)
            assert oldnodeinv is nodefwd
            invm[val] = nodefwd
            nodefwd.data = nodedata
        else:  # isdupval
            oldkey = nodeinv[val]
            oldval = _MISS
            oldnodefwd = fwdm.pop(oldkey)
            assert oldnodefwd is nodeinv
            fwdm[key] = nodeinv
            nodeinv.data = nodedata
        return _WriteResult(key, val, oldkey, oldval)

    def _undo_write(self, dedup_result, write_result):  # pylint: disable=too-many-locals
        fwdm = self._fwdm
        invm = self._invm
        isdupkey, isdupval, nodeinv, nodefwd = dedup_result
        key, val, oldkey, oldval = write_result
        if not isdupkey and not isdupval:
            self._pop(key)
        elif isdupkey and isdupval:
            # nodeinv.data was never changed, so it should still have its original item.
            assert nodeinv[oldkey] == val
            assert nodeinv[val] == oldkey
            # Restore original items.
            nodefwd.data = (key, oldval)
            nodeinv.prv.nxt = nodeinv.nxt.prv = nodeinv
            fwdm[oldkey] = invm[val] = nodeinv
            invm[oldval] = fwdm[key] = nodefwd
        elif isdupkey:
            nodefwd.data = (key, oldval)
            tmp = invm.pop(val)
            assert tmp is nodefwd
            invm[oldval] = nodefwd
            assert fwdm[key] is nodefwd
        else:  # isdupval
            nodeinv.data = (oldkey, val)
            tmp = fwdm.pop(key)
            assert tmp is nodeinv
            fwdm[oldkey] = nodeinv
            assert invm[val] is nodeinv

    def __iter__(self, reverse=False):
        """An iterator over this bidict's items in order."""
        fwdm = self._fwdm
        for node in _iter_nodes(self._sntl, reverse=reverse):
            korv, vork = node.data
            key = korv if node is fwdm.get(korv) else vork
            yield key

    def __reversed__(self):
        """An iterator over this bidict's items in reverse order."""
        for key in self.__iter__(reverse=True):
            yield key

    def equals_order_sensitive(self, other):
        """Order-sensitive equality check.

        *See also* :ref:`eq-order-insensitive`
        """
        if not isinstance(other, Mapping) or len(self) != len(other):
            return False
        return all(i == j for (i, j) in izip(iteritems(self), iteritems(other)))

    def __repr_delegate__(self):
        """See :meth:`bidict.BidictBase.__repr_delegate__`."""
        return list(iteritems(self))

    # Override the `values` implementation inherited from `Mapping`. Implemented in terms of
    # self.inv.keys(), so that on Python 3 we end up returning a KeysView (dict_keys) object.
    def values(self):
        """A set-like object providing a view on the contained values.

        Note that because the values of a :class:`~bidict.BidirectionalMapping`
        are the keys of its inverse,
        this returns a :class:`~collections.abc.KeysView`
        rather than a :class:`~collections.abc.ValuesView`,
        which has the advantages of constant-time containment checks
        and supporting set operations.
        """
        return self.inv.keys()

    if PY2:
        def viewvalues(self):  # noqa: D102; pylint: disable=missing-docstring
            return KeysView(self.inv)

        viewvalues.__doc__ = values.__doc__
        values.__doc__ = 'A list of the contained values.'

        def viewitems(self):
            """A set-like object providing a view on the contained items."""
            return ItemsView(self)

        def viewkeys(self):
            """A set-like object providing a view on the contained keys."""
            return KeysView(self)


#                             * Code review nav *
#==============================================================================
#  ← Prev: _bidict.py       Current: _orderedbase.py  Next: _frozenordered.py →
#==============================================================================

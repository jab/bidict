#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Bidirectional dict with convenient slice syntax: ``d[65] = 'A'`` ⇔
``d[:'A'] == 65``


Status
------------

.. image:: https://pypip.in/download/bidict/badge.svg
    :target: https://pypi.python.org/pypi/bidict
    :alt: Downloads per month

.. image:: https://pypip.in/version/bidict/badge.svg
    :target: https://pypi.python.org/pypi/bidict
    :alt: Latest release

.. image:: https://readthedocs.org/projects/bidict/badge/
    :target: https://bidict.readthedocs.org/
    :alt: Documentation

.. image:: https://travis-ci.org/jab/bidict.svg
    :target: https://travis-ci.org/jab/bidict
    :alt: Build status

.. image:: https://pypip.in/py_versions/bidict/badge.svg
    :target: https://pypi.python.org/pypi/bidict
    :alt: Supported Python versions

.. image:: https://pypip.in/implementation/bidict/badge.svg
    :target: https://pypi.python.org/pypi/bidict
    :alt: Supported Python implementations

.. image:: https://pypip.in/license/bidict/badge.svg
    :target: https://raw.githubusercontent.com/jab/bidict/master/LICENSE
    :alt: License
| 


Installation
------------

``pip install bidict``


Overview
--------

:mod:`bidict` provides a bidirectional mapping data structure and related
functionality to naturally work with one-to-one relations in Python.

Unlike other bidirectional dict libraries, ``bidict`` builds on top of the dict
API and supports the familiar ``__getitem__`` syntax. It also supports a
convenient slice syntax to express an inverse mapping::

    >>> element_by_symbol = bidict(H='hydrogen')
    >>> element_by_symbol['H']  # forward mapping works just like with dict
    'hydrogen'
    >>> element_by_symbol[:'hydrogen']  # use slice for the inverse mapping
    'H'

Syntax hacks ftw.


Motivation
----------

Python's built-in dict lets us associate unique keys with arbitrary values.
Because keys must be hashable, values can be looked up by key in constant time.
Different keys can map to the same value, but a single key cannot map to two
different values. For instance, ``{-1: 1, 0: 0, 1: 1}`` is a dict with
three unique keys and two unique values, because the keys -1 and 1 both map to
1. If you try to write its inverse ``{1: -1, 0: 0, 1: 1}``, the dict that
results has only two mappings, one for key 1 and one for key 0; since key 1
is not allowed to map to both -1 and 1, one of these mappings is discarded.

Sometimes the relation we're modeling will only ever have a single key mapping
to a single value, as in the relation of chemical elements and their symbols.
This is called a one-to-one (or injective) mapping (see
https://en.wikipedia.org/wiki/Injective_mapping).

In this case we can be sure that the inverse mapping has the same number of
items as the forward mapping, and moreover that if key k maps to value v in the
forward mapping, then v maps to k in the inverse. It would be useful then
to be able to look up, in constant time, keys by value, in addition to being
able to look up values by key. With the additional constraint that values must
also be hashable as well as keys, we can get constant-time forward and inverse
lookups -- with a convenient syntax to boot -- with ``bidict``.


More Examples
-------------

Expanding on the previous example, anywhere the ``__getitem__`` syntax can be
used to reference a forward mapping, slice syntax can be used too::

    >>> element_by_symbol['H'] = 'hydrogen'
    >>> element_by_symbol['H':]
    'hydrogen'

Including setting and deleting items in either direction::

    >>> element_by_symbol['He':] = 'helium'
    >>> element_by_symbol[:'lithium'] = 'Li'
    >>> del element_by_symbol['H':]
    >>> del element_by_symbol[:'lithium']
    >>> element_by_symbol
    bidict({'He': 'helium'})

The rest of the ``MutableMapping`` interface is also supported::

    >>> 'C' in element_by_symbol
    False
    >>> element_by_symbol.get('C', 'carbon')
    'carbon'
    >>> element_by_symbol.pop('He')
    'helium'
    >>> element_by_symbol
    bidict({})
    >>> element_by_symbol.update(Hg='mercury')
    >>> element_by_symbol
    bidict({'Hg': 'mercury'})

You can also use the unary inverse operator ~ on a ``bidict`` to get the
inverse mapping::

    >>> ~element_by_symbol
    bidict({'mercury': 'Hg'})

This is especially handy for composing with other operations::

    >>> 'mercury' in ~element_by_symbol
    True
    >>> (~element_by_symbol).pop('mercury')
    'Hg'

Because ``bidict`` maintains inverse mappings alongside forward mappings,
getting the inverse or composing an operation with the inverse costs only
constant time; the inverse does not have to be computed from scratch.
See the :class:`bidict.bidict` class for more documentation.

The ``inverted`` iterator is also provided in the spirit of the built-in
function ``reversed``. Pass in a mapping to get the inverse mapping, an
iterable of pairs to get the pairs' inverses, or any object implementing an
``__inverted__`` method. See the :class:`bidict.inverted` class for more
documentation.

``frozenbidict`` provides a hashable, immutable version of ``bidict`` making it
possible to insert into sets or mappings. See the :class:`bidict.frozenbidict`
class for more documentation.

The ``namedbidict`` class factory can be used to create a bidirectional mapping
with customized names for the forward and the inverse mappings accessible via
attributes. See :attr:`bidict.namedbidict` for more documentation.


Notes
-----

* It is intentional that the term "inverse" is used rather than "reverse".
  Consider a collection of (k, v) pairs. Taking the reverse of the collection
  can only be done if it is ordered, and (as the name says) reverses the order
  of the pairs in the collection. But, each original (k, v) pair remains in the
  resulting collection. By contrast, taking the inverse of such a collection
  does not require an original ordering, and does not make any claims about the
  ordering of the result, but rather just replaces every (k, v) pair with the
  inverse pair (v, k).

* "keys" and "values" could perhaps more properly be called "primary keys" and
  "secondary keys" (as in a database), or even "forward keys" and "inverse
  keys", respectively. ``bidict`` sticks with the terms "keys" and "values" for
  the sake of familiarity and to avoid potential confusion, but it's worth
  noting that values are also keys themselves. This allows us to return a
  set-like ``dict_keys`` object for :attr:`bidict.BidirectionalMapping.values`
  (Python 3) / :attr:`bidict.BidirectionalMapping.viewvalues` (Python 2),
  rather than a (non-set-like) ``dict_values`` object, for example.

* The built-in ``htmlentitydefs`` module provides an example of where
  ``bidict`` could be used in the Python standard library instead of having to
  maintain the two ``name2codepoint`` and ``codepoint2name`` dictionaries
  separately by hand.

  Another example from the standard library of where ``bidict`` would be
  useful is the ``logging._levelToName`` mapping.


Caveats
-------

* Because ``bidict`` is a bidirectional dict, values as well as keys must be
  hashable. Attempting to insert an unhashable value will result in an error::

    >>> anagrams_by_alphagram = bidict(opt=['opt', 'pot', 'top'])  # doctest: +ELLIPSIS
    Traceback (most recent call last):
    ...
    TypeError:...unhashable...
    >>> bidict(opt=('opt', 'pot', 'top'))
    bidict({'opt': ('opt', 'pot', 'top')})

* When instantiating or updating a ``bidict``, remember that mappings for
  like values with differing keys will be silently dropped (just as the dict
  literal ``{1: 'one', 1: 'uno'}`` silently drops a mapping), to maintain
  bidirectionality::

    >>> nils = bidict(zero=0, zilch=0, zip=0)
    >>> len(nils)
    1
    >>> nils.update(nix=0, nada=0)
    >>> len(nils)
    1

* When attempting to map the key of one existing mapping to the value of
  another (or vice versa), a ``CollapseException`` is raised to signal that the
  new mapping would cause the two existing mappings to silently collapse into
  the single new one::

    >>> b = bidict({0: 'zero', 1: 'one'})
    >>> b[0] = 'one'  # doctest: +ELLIPSIS +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
    ...
    CollapseException: ((0, 'zero'), (1, 'one'))
    >>> b
    bidict({0: 'zero', 1: 'one'})

  See :class:`bidict.CollapseException`.

  To prevent this in a case like the above, you can explicitly use the
  :attr:`bidict.bidict.forceput` method::

    >>> b.forceput(0, 'one')
    >>> b
    bidict({0: 'one'})

  Or use a ``collapsingbidict`` if you want a bidict which always allows
  collapsing mappings to proceed with no indication when they've occurred.
  See :class:`bidict.collapsingbidict` for examples.

* As with built-in dicts, mutating operations on a bidict are not atomic. So
  if you need to mutate the same bidict from two different threads, use a
  ``threading.Lock`` around mutating operations to synchronize access/prevent
  race conditions.
  See also: https://twitter.com/teozaurus/status/518071391959388160

* As documented below, a bidict ``b`` keeps a reference to its inverse bidict
  (accessible via ``b.inv``). By extension, its inverse bidict keeps a
  reference to it (``b.inv.inv is b``). So even when you no longer have any
  references to ``b``, its refcount will not drop to zero because its inverse
  still has a reference to it. Python's garbage collector will detect this and
  reclaim the memory allocated for a bidict when you no longer have any
  references to it. In other words, bidict won't leak memory as long as you
  don't ``gc.disable()``. If you do, reclaiming a bidict's memory is up to you.


Links
-----

* Documentation: https://bidict.readthedocs.org

* Development: https://github.com/jab/bidict

* License: https://raw.githubusercontent.com/jab/bidict/master/LICENSE


Credits
-------

* Thanks to Terry Reedy for the idea for the slice syntax.

* Thanks to Raymond Hettinger for the idea for namedbidict and pointing out
  various caveats.

* Thanks to Francis Carr for the idea of storing the inverse bidict.

See the rest of the bidict module for further documentation.
------------------------------------------------------------
"""

from sys import version_info

PY2 = version_info[0] == 2
if PY2:
    assert version_info[1] > 6, 'Python >= 2.7 required'

from collections import Hashable, Iterator, Mapping, MutableMapping
from re import compile as compile_re

if PY2:
    iteritems = lambda x: x.iteritems()
    viewitems = lambda x: x.viewitems()
else:
    iteritems = lambda x: iter(x.items())
    viewitems = lambda x: x.items()

def fancy_iteritems(*map_or_it, **kw):
    """
    Generator yielding the mappings provided.
    Abstracts differences between Python 2 and 3::

        >>> it = fancy_iteritems({1: 2})
        >>> next(it)
        (1, 2)
        >>> next(it)
        Traceback (most recent call last):
            ...
        StopIteration

    Accepts zero or one positional argument which it first tries iterating over
    as a mapping (as above), and if that fails, falls back to iterating over as
    a sequence, yielding items two at a time::

        >>> it = fancy_iteritems([(1, 2), (3, 4)])
        >>> next(it)
        (1, 2)
        >>> next(it)
        (3, 4)
        >>> next(it)
        Traceback (most recent call last):
            ...
        StopIteration
        >>> list(fancy_iteritems())
        []

    Mappings may also be passed as keyword arguments, which will be yielded
    after any mappings passed via positional argument::

        >>> list(sorted(fancy_iteritems(a=1, b=2)))
        [('a', 1), ('b', 2)]
        >>> list(sorted(fancy_iteritems({'a': 1}, b=2, c=3)))
        [('a', 1), ('b', 2), ('c', 3)]
        >>> list(sorted(fancy_iteritems([('a', 1)], b=2, c=3)))
        [('a', 1), ('b', 2), ('c', 3)]

    In other words, this is like a generator analog of the dict constructor.

    Note that if any mappings from a sequence or keyword argument repeat an
    earlier mapping in the positional argument, repeat mappings will still
    be yielded, whereas with ``dict`` the last repeat clobbers earlier ones::

        >>> dict([('a', 1), ('a', 2)])
        {'a': 2}
        >>> list(fancy_iteritems([('a', 1), ('a', 2)]))
        [('a', 1), ('a', 2)]
        >>> dict([('a', 1), ('a', 2)], a=3)
        {'a': 3}
        >>> list(fancy_iteritems([('a', 1), ('a', 2)], a=3))
        [('a', 1), ('a', 2), ('a', 3)]
    """
    if map_or_it:
        l = len(map_or_it)
        if l != 1:
            raise TypeError('expected at most 1 argument, got %d' % l)
        map_or_it = map_or_it[0]
        try:
            it = iteritems(map_or_it)   # mapping?
        except AttributeError:          #  no
            for (k, v) in map_or_it:    #    -> treat as sequence
                yield (k, v)
        else:                           #  yes
            for (k, v) in it:           #    -> treat as mapping
                yield (k, v)
    for (k, v) in iteritems(kw):
        yield (k, v)


class inverted(Iterator):
    """
    An iterator in the spirit of ``reversed``. Useful for inverting a mapping::

        >>> keys = (1, 2, 3)
        >>> vals = ('one', 'two', 'three')
        >>> fwd = dict(zip(keys, vals))
        >>> inv = dict(inverted(fwd))
        >>> inv == dict(zip(vals, keys))
        True

    Passing an iterable of pairs produces an iterable of the pairs' inverses::

        >>> seq = [(1, 'one'), (2, 'two'), (3, 'three')]
        >>> list(inverted(seq))
        [('one', 1), ('two', 2), ('three', 3)]

    Passing an ``inverted`` object back into ``inverted`` produces the original
    sequence of pairs::

        >>> seq == list(inverted(inverted(seq)))
        True

    Under the covers, ``inverted`` first tries to call ``__inverted__`` on the
    wrapped object and returns the result if the call succeeded, creating
    synergy with :attr:`bidict.BidirectionalMapping.__inverted__` (effectively
    delegating to the class if it supports inverting natively). If the call
    fails, ``inverted`` falls back on calling its own ``__next__`` method,
    which in turn calls :attr:`bidict.fancy_iteritems` on the wrapped object,
    yielding the inverse of the pairs that fancy_iteritems yields.

    Be careful with passing the inverse of a non-injective mapping into
    ``dict``; mappings for like values with differing keys will be dropped
    silently, just as ``{1: 'one', 1: 'uno'}`` silently drops a mapping::

        >>> squares = {-2: 4, -1: 1, 0: 0, 1: 1, 2: 4}
        >>> len(squares)
        5
        >>> len(dict(inverted(squares)))
        3
    """

    def __init__(self, data):
        self._data = data

    def __iter__(self):
        try:
            it = self._data.__inverted__
        except AttributeError:
            it = self.__next__
        return it()

    def __next__(self):
        for (k, v) in fancy_iteritems(self._data):
            yield (v, k)

    # compat
    if PY2:
        next = __next__


class CollapseException(Exception):
    """
    Exception raised by :class:`bidict.bidict` when attempting to insert a new
    mapping that would collapse two existing mappings::

        >>> b = bidict({1: 'one', 2: 'two'})
        >>> b[1] = 'two'  # doctest: +ELLIPSIS +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
        ...
        CollapseException: ((1, 'one'), (2, 'two'))
        >>> b[:'two'] = 1  # doctest: +ELLIPSIS +IGNORE_EXCEPTION_DETAIL
        Traceback (most recent call last):
        ...
        CollapseException: ((1, 'one'), (2, 'two'))

    Notice the exception instance's args are set to the two existing mappings
    that would have been collapsed by inserting the new mapping.
    """

_none = object()
class BidirectionalMapping(Mapping):
    """
    The read-only functionality of ``bidict`` is implemented in this base
    class. :class:`bidict.bidict` and :class:`bidict.frozenbidict` both extend
    this.
    """
    def __init__(self, *args, **kw):
        self._fwd = {}
        self._bwd = {}
        for (k, v) in fancy_iteritems(*args, **kw):
            self._put(k, v)
        inv = object.__new__(self.__class__)
        inv._fwd = self._bwd
        inv._bwd = self._fwd
        inv._inv = self
        self._inv = inv
        self._hash = None

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self._fwd)
    __str__ = __repr__

    def __eq__(self, other):
        """
        Supports equality testing with another mapping::

            >>> d = dict(a=1)
            >>> b = bidict(a=1)
            >>> b == d
            True
            >>> f = frozenbidict(a=1)
            >>> f == d
            True
            >>> ElementMap = namedbidict('ElementMap', 'symbol', 'element')
            >>> noble_gases = ElementMap(He='helium')
            >>> noble_gases == dict(He='helium')
            True

        Even works with nan::

            >>> nan = float('nan')
            >>> bidict({nan: 1}) == {nan: 1}
            True

        Comparing with a non-mapping returns False:

            >>> bidict(a=1) == [('a', 1)]
            False
        """
        try:
            return viewitems(self) == viewitems(other)
        except:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __invert__(self):
        """
        Called when the unary inverse operator (~) is applied.
        """
        return self._inv

    inv = property(__invert__, doc='Property providing access to the inverse '\
        'bidict. Can be chained as in: ``B.inv.inv is B``')

    def __inverted__(self):
        return iteritems(self._bwd)

    @staticmethod
    def _fwd_slice(slice):
        """
        Raises ``TypeError`` if the given slice does not have either only
        its start or only its stop set to a non-None value.

        Returns True if only its start is not None and False if only its stop
        is not None.
        """
        if slice.step is not None or \
            (not ((slice.start is None) ^ (slice.stop is None))):
            raise TypeError('Slice must specify only either start or stop')
        return slice.start is not None

    def __getitem__(self, keyorslice):
        if isinstance(keyorslice, slice):
            # forward lookup (by key): b[key:]
            if self._fwd_slice(keyorslice):
                return self._fwd[keyorslice.start]
            else:  # inverse lookup (by val): b[:val]
                return self._bwd[keyorslice.stop]
        else:  # keyorslice is a key: b[key]
            return self._fwd[keyorslice]

    def _put(self, key, val):
        try:
            oldval = self._fwd[key]
        except KeyError:
            oldval = _none
        try:
            oldkey = self._bwd[val]
        except KeyError:
            oldkey = _none

        if oldval is not _none and oldkey is not _none:
            if key == oldkey and val == oldval:
                return
            raise CollapseException((key, oldval), (oldkey, val))
        elif oldval is not _none:
            del self._bwd[oldval]
        elif oldkey is not _none:
            del self._fwd[oldkey]

        self._fwd[key] = val
        self._bwd[val] = key

    get = lambda self, k, *args: self._fwd.get(k, *args)
    copy = lambda self: self.__class__(self._fwd)
    get.__doc__ = dict.get.__doc__
    copy.__doc__ = dict.copy.__doc__
    __len__ = lambda self: len(self._fwd)
    __iter__ = lambda self: iter(self._fwd)
    __contains__ = lambda self, x: x in self._fwd
    __len__.__doc__ = dict.__len__.__doc__
    __iter__.__doc__ = dict.__iter__.__doc__
    __contains__.__doc__ = dict.__contains__.__doc__
    keys = lambda self: self._fwd.keys()
    items = lambda self: self._fwd.items()
    keys.__doc__ = dict.keys.__doc__
    items.__doc__ = dict.items.__doc__
    values = lambda self: self._bwd.keys()
    values.__doc__ = \
        "D.values() -> a set-like object providing a view on D's values. " \
        "Note that because values of a BidirectionalMapping are also keys, " \
        "this returns a ``dict_keys`` object rather than a ``dict_values`` " \
        "object."
    if PY2:
        iterkeys = lambda self: self._fwd.iterkeys()
        viewkeys = lambda self: self._fwd.viewkeys()
        iteritems = lambda self: self._fwd.iteritems()
        viewitems = lambda self: self._fwd.viewitems()
        itervalues = lambda self: self._bwd.iterkeys()
        viewvalues = lambda self: self._bwd.viewkeys()
        iterkeys.__doc__ = dict.iterkeys.__doc__
        viewkeys.__doc__ = dict.viewkeys.__doc__
        iteritems.__doc__ = dict.iteritems.__doc__
        viewitems.__doc__ = dict.viewitems.__doc__
        itervalues.__doc__ = dict.itervalues.__doc__
        viewvalues.__doc__ = values.__doc__.replace('values()', 'viewvalues()')
        values.__doc__ = dict.values.__doc__


class frozenbidict(BidirectionalMapping, Hashable):
    """
    Extends ``BidirectionalMapping`` and ``Hashable`` to provide an immutable,
    hashable bidict. It's immutable simply because it doesn't implement any
    mutating methods::

        >>> f = frozenbidict()
        >>> f.update(H='hydrogen')  # doctest: +ELLIPSIS
        Traceback (most recent call last):
        ...
        AttributeError...
        >>> f['C'] = 'carbon'  # doctest: +ELLIPSIS
        Traceback (most recent call last):
        ...
        TypeError...

    And, unlike ``BidirectionalMapping`` and ``bidict``, it's hashable simply
    because it implements ``__hash__``::

        >>> b = bidict(H='hydrogen')
        >>> h = hash(b)  # doctest: +ELLIPSIS
        Traceback (most recent call last):
        ...
        TypeError...
        >>> f = frozenbidict(b)
        >>> hash(f) is not 'an exception'
        True

    Hashability allows for insertion into sets, mappings, etc. and associated
    hashing semantics::

        >>> d = {}
        >>> d[f] = 'hashable!'
        >>> g = frozenbidict(H='hydrogen')
        >>> hash(f) == hash(g)
        True
        >>> f is g
        False

    To compute a frozenbidict's hash value, a temporary frozenset is
    constructed out of the frozenbidict's items, and the hash of the frozenset
    is returned. So be aware that computing a frozenbidict's hash is not
    a constant-time or -space operation.

    To mitigate this, the hash is computed lazily, only when ``__hash__`` is
    first called, and is then cached so that future calls take constant time.
    """
    def __hash__(self):
        if self._hash is None:
            self._hash = hash(frozenset(viewitems(self)))
        return self._hash


class bidict(BidirectionalMapping, MutableMapping):
    """
    Extends :class:`bidict.BidirectionalMapping` to implement the
    ``MutableMapping`` interface. The API is a superset of the ``dict`` API
    minus the ``fromkeys`` method, which doesn't make sense for a bidirectional
    mapping because keys *and* values must be unique.

    Examples::

        >>> keys = (1, 2, 3)
        >>> vals = ('one', 'two', 'three')
        >>> bi = bidict(zip(keys, vals))
        >>> bi == bidict({1: 'one', 2: 'two', 3: 'three'})
        True
        >>> bidict(inverted(bi)) == bidict(zip(vals, keys))
        True

    You can use standard subscripting syntax with a key to get or set a forward
    mapping::

        >>> bi[2]
        'two'
        >>> bi[2] = 'twain'
        >>> bi[2]
        'twain'
        >>> bi[4]
        Traceback (most recent call last):
            ...
        KeyError: 4

    Or use a slice with only a ``start``::

        >>> bi[2:]
        'twain'
        >>> bi[0:] = 'naught'
        >>> bi[0:]
        'naught'

    Use a slice with only a ``stop`` to get or set an inverse mapping::

        >>> bi[:'one']
        1
        >>> bi[:'aught'] = 1
        >>> bi[:'aught']
        1
        >>> bi[1]
        'aught'
        >>> bi[:'one']
        Traceback (most recent call last):
            ...
        KeyError: 'one'

    Deleting items from the bidict works the same way::

        >>> del bi[0]
        >>> del bi[2:]
        >>> del bi[:'three']
        >>> bi
        bidict({1: 'aught'})

    bidicts maintain references to their inverses via the ``inv`` property,
    which can also be used to access or modify them::

        >>> bi.inv
        bidict({'aught': 1})
        >>> bi.inv['aught']
        1
        >>> bi.inv[:1]
        'aught'
        >>> bi.inv[:1] = 'one'
        >>> bi.inv
        bidict({'one': 1})
        >>> bi
        bidict({1: 'one'})
        >>> bi.inv.inv is bi
        True
        >>> bi.inv.inv.inv is bi.inv
        True

    A ``bidict``’s inverse can also be accessed via the unary ~ operator, by
    analogy to the unary bitwise inverse operator::

        >>> ~bi
        bidict({'one': 1})
        >>> ~bi is bi.inv
        True

    Because ~ binds less tightly than brackets, parentheses are necessary for
    something like::

        >>> (~bi)['one']
        1

    bidicts work with ``inverted`` as expected::

        >>> biinv = bidict(inverted(bi))
        >>> biinv
        bidict({'one': 1})

    This of course creates a new object (equivalent but not identical)::

        >>> biinv == bi.inv
        True
        >>> biinv is bi.inv
        False

    Notice that ``__eq__`` has been implemented to make == work as expected.

    Inverting the inverse should round-trip::

        >>> bi == bidict(inverted(inverted(bi)))
        True

    Use ``invert`` to invert the mapping in place, in constant time::

        >>> bi.invert()
        >>> bi
        bidict({'one': 1})

    The rest of the ``MutableMapping`` interface is supported too::

        >>> bi.get('one')
        1
        >>> bi.get('zero')
        >>> bi.get('zero', 0)
        0
        >>> list(bi.keys())
        ['one']
        >>> list(bi.values())
        [1]
        >>> list(bi.items())
        [('one', 1)]
        >>> bi.setdefault('one', 2)
        1
        >>> bi.setdefault('two', 2)
        2
        >>> bi.pop('one')
        1
        >>> bi.popitem()
        ('two', 2)
        >>> bi.inv.setdefault(3, 'three')
        'three'
        >>> bi
        bidict({'three': 3})
        >>> len(bi)  # calls __len__
        1
        >>> [key for key in bi]  # calls __iter__, returns keys like dict
        ['three']
        >>> 'three' in bi  # calls __contains__
        True
        >>> list(bi.keys())
        ['three']
        >>> list(bi.values())
        [3]
        >>> bi.update([('four', 4)])
        >>> bi.update({'five': 5}, six=6, seven=7)
        >>> sorted(bi.items(), key=lambda x: x[1])
        [('three', 3), ('four', 4), ('five', 5), ('six', 6), ('seven', 7)]

    When instantiating or updating a ``bidict``, remember that mappings for
    like values with differing keys will be silently dropped (just as the
    literal ``{1: 'one', 1: 'uno'}`` silently drops a mapping), to maintain
    bidirectionality::

        >>> nils = bidict(zero=0, zilch=0, zip=0)
        >>> len(nils)
        1
        >>> nils.update(nix=0, nada=0)
        >>> len(nils)
        1
    """
    def _del(self, key):
        val = self._fwd[key]
        del self._fwd[key]
        del self._bwd[val]

    def __delitem__(self, keyorslice):
        if isinstance(keyorslice, slice):
            # delete by key: del b[key:]
            if self._fwd_slice(keyorslice):
                self._del(keyorslice.start)
            else:  # delete by value: del b[:val]
                self._del(self._bwd[keyorslice.stop])
        else:  # keyorslice is a key: del b[key]
            self._del(keyorslice)

    def __setitem__(self, keyorslice, keyorval):
        if isinstance(keyorslice, slice):
            # keyorslice.start is key, keyorval is val: b[key:] = val
            if self._fwd_slice(keyorslice):
                self._put(keyorslice.start, keyorval)
            else:  # keyorval is key, keyorslice.stop is val: b[:val] = key
                self._put(keyorval, keyorslice.stop)
        else:  # keyorslice is a key, keyorval is a val: b[key] = val
            self._put(keyorslice, keyorval)

    def put(self, key, val):
        """
        Alternative to using the setitem syntax to insert a mapping::

            >>> b = bidict()
            >>> b.put('H', 'hydrogen')
            >>> b
            bidict({'H': 'hydrogen'})
        """
        self._put(key, val)

    def forceput(self, key, val):
        """
        Like :attr:`bidict.bidict.put` but silently removes any existing
        mapping that would otherwise cause a :class:`CollapseException`
        before inserting the given mapping::

            >>> b = bidict({0: 'zero', 1: 'one'})
            >>> b.put(0, 'one')  # doctest: +ELLIPSIS +IGNORE_EXCEPTION_DETAIL
            Traceback (most recent call last):
            ...
            CollapseException: ((0, 'zero'), (1, 'one'))
            >>> b.forceput(0, 'one')
            >>> b
            bidict({0: 'one'})
        """
        oldval = self._fwd.get(key, _none)
        oldkey = self._bwd.get(val, _none)
        if oldval is not _none:
            del self._bwd[oldval]
        if oldkey is not _none:
            del self._fwd[oldkey]
        self._fwd[key] = val
        self._bwd[val] = key

    def clear(self):
        self._fwd.clear()
        self._bwd.clear()

    def invert(self):
        self._fwd, self._bwd = self._bwd, self._fwd
        self._inv._fwd, self._inv._bwd = self._inv._bwd, self._inv._fwd

    def pop(self, key, *args):
        val = self._fwd.pop(key, *args)
        del self._bwd[val]
        return val

    def popitem(self):
        if not self._fwd:
            raise KeyError
        key, val = self._fwd.popitem()
        del self._bwd[val]
        return key, val

    def setdefault(self, key, default=None):
        val = self._fwd.setdefault(key, default)
        self._bwd[val] = key
        return val

    def update(self, *args, **kw):
        for k, v in fancy_iteritems(*args, **kw):
            self[k] = v


class collapsingbidict(bidict):
    """
    A bidict which does not throw a :class:`bidict.CollapseException` when
    attempting to insert a new mapping that would collapse two existing
    mappings::

        >>> b = collapsingbidict({1: 'one', 2: 'two'})
        >>> b[1] = 'two'
        >>> b
        collapsingbidict({1: 'two'})
    """
    _put = bidict.forceput

_LEGALNAMEPAT = '^[a-zA-Z][a-zA-Z0-9_]*$'
_LEGALNAMERE = compile_re(_LEGALNAMEPAT)

def _empty_namedbidict(mapname, fwdname, invname):
    """
    Create an empty instance of a custom bidict (namedbidict). This method is
    used to make ``namedbidict`` instances picklable.
    """
    return namedbidict(mapname, fwdname, invname)()

def namedbidict(mapname, fwdname, invname, bidict_type=bidict):
    """
    Generate a custom bidict class in the spirit of ``namedtuple`` with
    custom attribute-based access to forward and inverse mappings::

        >>> ElementMap = namedbidict('ElementMap', 'symbol', 'element')
        >>> noble_gases = ElementMap(He='helium')
        >>> noble_gases.element_for['He']
        'helium'
        >>> noble_gases.symbol_for['helium']
        'He'
        >>> noble_gases.element_for['Ne'] = 'neon'
        >>> del noble_gases.symbol_for['helium']
        >>> noble_gases
        ElementMap({'Ne': 'neon'})

    Pass to ``bidict`` to get back a regular ``bidict``::

        >>> bidict(noble_gases)
        bidict({'Ne': 'neon'})

    Comparison works as expected::

        >>> noble_gases2 = ElementMap({'Ne': 'neon'})
        >>> noble_gases2 == noble_gases
        True
        >>> noble_gases2 == bidict(noble_gases)
        True
        >>> noble_gases2 == dict(noble_gases)
        True
        >>> noble_gases2['Rn'] = 'radon'
        >>> noble_gases2 == noble_gases
        False
        >>> noble_gases2 != noble_gases
        True
        >>> noble_gases2 != bidict(noble_gases)
        True
        >>> noble_gases2 != dict(noble_gases)
        True

    The ``bidict_type`` keyword arg allows overriding the BidirectionalMapping
    type used, useful for creating e.g. a namedfrozenbidict::

        >>> ElMap = namedbidict('ElMap', 'sym', 'el', bidict_type=frozenbidict)
        >>> noble = ElMap(He='helium')
        >>> hash(noble) is not 'an exception'
        True
        >>> noble['C'] = 'carbon'  # doctest: +ELLIPSIS
        Traceback (most recent call last):
        ...
        TypeError...
    """
    for name in mapname, fwdname, invname:
        if _LEGALNAMERE.match(name) is None:
            raise ValueError('"%s" does not match pattern %s' %
                             (name, _LEGALNAMEPAT))

    for_fwd = invname + '_for'
    for_inv = fwdname + '_for'
    __dict__ = {for_fwd: property(lambda self: self),
                for_inv: bidict_type.inv}

    custombidict = type(mapname, (bidict_type,), __dict__)

    # support pickling
    custombidict.__reduce__ = lambda self: \
        (_empty_namedbidict, (mapname, fwdname, invname), self.__dict__)

    return custombidict


if __name__ == '__main__':
    from doctest import testmod
    testmod()

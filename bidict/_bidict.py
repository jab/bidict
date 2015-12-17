from ._common import BidirectionalMapping
from .util import pairs
from collections import MutableMapping


class bidict(BidirectionalMapping, MutableMapping):
    """
    Mutable bidirectional map type.
    """
    def _del(self, key):
        val = self._fwd[key]
        del self._fwd[key]
        del self._bwd[val]

    def __delitem__(self, key):
        """
        Analogous to dict.__delitem__(), keeping bidirectionality intact.
        """
        self._del(key)

    def __setitem__(self, key, val):
        """
        Sets the value for ``key`` to ``val``.

        If ``key`` is already associated with a different value,
        the old value will be replaced with ``val``.
        Use :attr:`put` to raise an exception in this case instead.

        If ``val`` is already associated with a different key,
        an exception is raised
        to protect against accidentally replacing the existing mapping.

        If ``key`` is already associated with ``val``, this is a no-op.

        Use :attr:`forceput` to unconditionally associate ``key`` with ``val``,
        replacing any existing mappings necessary to preserve uniqueness.

        :raises ValueExistsException: if attempting to set a mapping with a
            non-unique value.
        """
        self._put(key, val, overwrite_key=False, overwrite_val=True)

    def put(self, key, val):
        """
        Inserts the given mapping iff
        ``key`` is not already associated with an existing value and
        ``val`` is not already associated with an existing key.

        If ``key`` is already associated with ``val``, this is a no-op.

        :raises KeyExistsException: if attempting to insert a mapping with the
            same key as an existing mapping.

        :raises ValueExistsException: if attempting to insert a mapping with
            the same value as an existing mapping.
        """
        self._put(key, val, overwrite_key=False, overwrite_val=False)

    def forceput(self, key, val):
        """
        Associates ``key`` with ``val``,
        replacing any existing mappings with ``key`` or ``val``
        necessary to preserve uniqueness.
        """
        self._put(key, val, overwrite_key=True, overwrite_val=True)

    def clear(self):
        """
        Removes all items.
        """
        self._fwd.clear()
        self._bwd.clear()

    def pop(self, key, *args):
        """
        Analogous to dict.pop(), keeping bidirectionality intact.
        """
        val = self._fwd.pop(key, *args)
        del self._bwd[val]
        return val

    def popitem(self):
        """
        Analogous to dict.popitem(), keeping bidirectionality intact.
        """
        if not self._fwd:
            raise KeyError('popitem(): %s is empty' % self.__class__.__name__)
        key, val = self._fwd.popitem()
        del self._bwd[val]
        return key, val

    def setdefault(self, key, default=None):
        """
        Analogous to dict.setdefault(), keeping bidirectionality intact.
        """
        val = self._fwd.setdefault(key, default)
        self._bwd[val] = key
        return val

    def update(self, *args, **kw):
        """
        Analogous to dict.update(), keeping bidirectionality intact.

        Like calling :attr:`__setitem__` for each mapping given.

        :raises ValueExistsException: if attempting to insert a mapping with a
            non-unique value.
        """
        return self._update(*args, **kw)

    def forceupdate(self, *args, **kw):
        """
        Calls :attr:`forceput` for each mapping given.
        """
        for k, v in pairs(*args, **kw):
            self.forceput(k, v)

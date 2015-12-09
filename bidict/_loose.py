from ._bidict import bidict

class loosebidict(bidict):
    """
    A mutable bidict which always uses forcing put operations so that it never
    raises :class:`KeyExistsException` or :class:`ValueExistsException`.
    """
    _ignored = object()
    def _put(self, key, val, overwrite_key=_ignored, overwrite_val=_ignored):
        return super(self.__class__, self)._put(
            key, val, overwrite_key=True, overwrite_val=True)

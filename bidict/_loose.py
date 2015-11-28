from ._bidict import bidict

class loosebidict(bidict):
    """
    A mutable bidict which always uses forcing put operations
    so that it never raises :class:`bidict.ValueExistsException`.
    """
    def _put(self, key, val):
        return self.forceput(key, val)

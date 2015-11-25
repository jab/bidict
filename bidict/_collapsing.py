from ._bidict import bidict

class collapsingbidict(bidict):
    """
    A mutable bidict which does not raise :class:`bidict.CollapseException`
    but rather allows collapses to succeed without warning.
    """
    def _put(self, key, val):
        return super(self.__class__, self).forceput(key, val)

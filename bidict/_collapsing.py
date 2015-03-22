from ._bidict import bidict

class collapsingbidict(bidict):
    """
    A mutable bidict which does not throw a :class:`bidict.CollapseException`
    when an update would cause two existing mappings to collapse,
    but rather allows the update to succeed
    with no explicit sign that two mappings just collapsed into one::

        >>> b = collapsingbidict({0: 'zero', 1: 'one'})
        >>> b[0] = 'one'
        >>> b
        collapsingbidict({0: 'one'})

    """
    _put = bidict.forceput

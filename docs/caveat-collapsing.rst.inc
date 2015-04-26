.. _caveat-collapsing:

Collapsing Mappings
-------------------

Consider the following::

    >>> b = bidict({0: 'zero', 1: 'one'})
    >>> b[0] = 'one'

What should happen next?

We could just let this happen::

    >>> b
    bidict({0: 'one'})

In other words,
we could silently collapse the two existing mappings together
into the new one we're setting,
preserving uniqueness of keys and values.
But there are two problems with this.

- Users who haven't considered this case before
  may not realize that updating an existing mapping
  could end up implicitly deleting another mapping.
  This behavior could slip past them and then come back to bite them later.

- Users who need to detect when this would happen
  and only update the mapping conditionally
  would have to litter their code with ugly containment checks.

Instead, :class:`bidict.bidict` rejects the update
and throws a :class:`bidict.CollapseException`::

    Traceback (most recent call last):
    ...
    CollapseException: ((0, 'zero'), (1, 'one'))
    >>> b
    bidict({0: 'zero', 1: 'one'})

This gives users a clean API for detecting this case,
and makes sure it's handled intentionally.

Moreover, bidict provides better options for when you want collapsing behavior:

- Explicitly use the :attr:`bidict.bidict.forceput` method::

    >>> b.forceput(0, 'one')
    >>> b
    bidict({0: 'one'})

- Use a :class:`bidict.collapsingbidict` instead.

Values Must Be Hashable
-----------------------

Because you must be able to look up keys by value as well as values by key,
values must also be hashable.

Attempting to insert an unhashable value will result in an error::

    >>> anagrams_by_alphagram = bidict(opt=['opt', 'pot', 'top'])
    Traceback (most recent call last):
    ...
    TypeError:...unhashable...
    >>> bidict(opt=('opt', 'pot', 'top'))
    bidict({'opt': ('opt', 'pot', 'top')})

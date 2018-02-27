Values Must Be Hashable
+++++++++++++++++++++++

Because you must be able to look up keys by value as well as values by key,
values must also be hashable.

Attempting to insert an unhashable value will result in an error::

    >>> anagrams_by_alphagram = dict(opt=['opt', 'pot', 'top'])
    >>> from bidict import bidict
    >>> bidict(anagrams_by_alphagram)
    Traceback (most recent call last):
    ...
    TypeError: ...

So in this example,
using a tuple or a frozenset instead of a list would do the trick::

    >>> bidict(opt=('opt', 'pot', 'top'))
    bidict({'opt': ('opt', 'pot', 'top')})

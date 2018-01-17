.. _inv-avoids-reference-cycles:

:attr:`~bidict.BidirectionalMapping.inv` Avoids Reference Cycles
----------------------------------------------------------------

A careful reader might notice the following...

    >>> from bidict import bidict
    >>> fwd = bidict(one=1)
    >>> inv = fwd.inv
    >>> inv.inv is fwd
    True

...and become concerned that a bidict and its inverse create a reference cycle.
If this were true, in CPython this would mean that the memory for a bidict
could not be immediately reclaimed when you retained no more references to it,
but rather would have to wait for the next gargage collection to kick in
before it could be reclaimed.

However, under the hood bidict uses a :class:`weakref.ref`
to store the inverse reference in one direction,
avoiding the strong reference cycle.
As a result, when you no longer retain any references to a bidict you create,
you can be sure that its refcount in CPython drops to zero,
and that its memory will therefore be reclaimed immediately.

.. note::

   In PyPy this is not an issue, as PyPy doesn't use reference counts.
   The memory for unreferenced objects in PyPy is only reclaimed
   when GC kicks in, which is unpredictable.

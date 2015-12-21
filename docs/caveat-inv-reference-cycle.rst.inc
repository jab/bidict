Bidicts Create Reference Cycles
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

As we've seen,
a bidict *b* keeps a reference to its inverse *b.inv*,
and its inverse bidict keeps a reference to it (*b.inv.inv is b*).
So even when you no longer have any references to *b*,
its refcount will not drop to zero
because its inverse still has a reference to it.
Python's garbage collector will detect this
and reclaim the memory allocated for a bidict
when you no longer have any references to it.

**NOTE:** Prior to Python 3.4,
*__del__()* methods prevented reference cycles from being garbage collected.
No bidicts implement *__del__()*,
so this is only an issue if you implement *__del__()* in a bidict subclass.

Non-atomic Mutation
^^^^^^^^^^^^^^^^^^^

As with built-in dicts, mutating operations on a bidict are not atomic.
If you need to mutate the same bidict from different threads,
use a
`synchronization primitive <https://docs.python.org/3/library/threading.html#lock-objects>`_
to coordinate access. [#]_

.. [#] *See also:* `[2] <https://twitter.com/teozaurus/status/518071391959388160>`_

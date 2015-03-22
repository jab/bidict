.. _caveat-frozenbidict-hash:

Hashing frozenbidicts
^^^^^^^^^^^^^^^^^^^^^

To compute a frozenbidict's hash value,
a temporary frozenset is constructed out of the frozenbidict's items,
and the hash of the frozenset is returned.
So be aware that requesting a frozenbidict's hash
may not be a constant-time or -space operation.

To mitigate this, the hash is computed lazily only when first called,
and is then cached so that future calls take constant time.

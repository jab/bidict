.. _performance:

Performance
-----------

bidict strives to be as performant as possible
while being faithful to its purpose.
The need for speed
is balanced with the responsibility
to protect users from shooting themselves in the foot.

In general,
accomplishing some task using bidict
should have about the same performance
as keeping two inverse dicts in sync manually.
The test suite includes benchmarks for common workloads
to catch any performance regressions.

If you spot a case where bidict's performance could be improved,
please don't hesitate to
:ref:`file an issue or submit a pull request <contributing>`.

.. _performance:

Performance
===========

bidict strives to be as performant as possible
while being faithful to its purpose.
In general,
accomplishing some task using bidict
should have about the same performance
as keeping two inverse dicts in sync manually.
The test suite includes benchmarks to verify this
for some common workloads.
If bidict ever fails to achieve
equivalent asymptotic time and space complexity
for general use cases,
it should be considered a performance regression
and reported in the `issue tracker <https://github.com/jab/bidict/issues>`_.

Now let's check out the :ref:`other bidict types <other-bidict-types>`.

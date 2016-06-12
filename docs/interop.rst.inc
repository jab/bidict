Interop
+++++++

bidicts interoperate well with other types of mappings.
For example, they support (efficient) polymorphic equality testing::

    >>> from bidict import bidict
    >>> bidict(a=1) == dict(a=1)
    True

And converting back and forth works as expected
(modulo any value duplication, as discussed above)::

    >>> dict(bidict(a=1))
    {'a': 1}
    >>> bidict(dict(a=1))
    bidict({'a': 1})

See the :ref:`polymorphism` section for more interoperability documentation.

.. Forward declarations for all the custom interpreted text roles that
   Sphinx defines and that are used below. This helps Sphinx-unaware tools
   (e.g. rst2html, PyPI's and GitHub's renderers, etc.).
.. role:: doc
.. role:: ref


Changelog
=========

Release Notifications
---------------------

.. duplicated in README.rst
   (would use `.. include::` but GitHub doesn't understand it)

.. image:: https://img.shields.io/badge/libraries.io-subscribe-5BC0DF.svg
   :target: https://libraries.io/pypi/bidict
   :alt: Follow on libraries.io

Tip: Subscribe to releases
`on GitHub <https://github.blog/changelog/2018-11-27-watch-releases/>`__ or
`libraries.io <https://libraries.io/pypi/bidict>`__
to be notified when new versions of ``bidict`` are released.


0.21.2 (2020-09-07)
-------------------

- Include `py.typed <https://www.python.org/dev/peps/pep-0561/#packaging-type-information>`__
  file to mark :mod:`bidict` as type hinted.


0.21.1 (2020-09-07)
-------------------

This release was yanked and replaced with the 0.21.2 release,
which actually provides the intended changes.


0.21.0 (2020-08-22)
-------------------

- :mod:`bidict` now provides
  `type hints <https://www.python.org/dev/peps/pep-0484/>`__! ⌨️ ✅

  Adding type hints to :mod:`bidict` poses particularly interesting challenges
  due to the combination of generic types,
  dynamically-generated types
  (such as :ref:`inverse bidict classes <extending:Dynamic Inverse Class Generation>`
  and :func:`namedbidicts <bidict.namedbidict>`),
  and complicating optimizations
  such as the use of slots and weakrefs.

  It didn't take long to hit bugs and missing features
  in the state of the art for type hinting in Python today,
  e.g. missing higher-kinded types support
  (`python/typing#548 <https://github.com/python/typing/issues/548#issuecomment-621195693>`__),
  too-narrow type hints for :class:`collections.abc.Mapping`
  (`python/typeshed#4435 <https://github.com/python/typeshed/issues/4435>`__),
  a :class:`typing.Generic` bug in Python 3.6
  (`BPO-41451 <https://bugs.python.org/issue41451>`__), etc.

  That said, this release should provide a solid foundation
  for code using :mod:`bidict` that enables static type checking.

  As always, if you spot any opportunities to improve :mod:`bidict`
  (including its new type hints),
  please don't hesitate to submit a PR!

- Add :class:`bidict.MutableBidirectionalMapping` ABC.

  The :ref:`other-bidict-types:Bidict Types Diagram` has been updated accordingly.

- Drop support for Python 3.5,
  which reaches end of life on 2020-09-13,
  represents a tiny percentage of bidict downloads on
  `PyPI Stats <https://pypistats.org/packages/bidict>`__,
  and lacks support for
  `variable type hint syntax <https://www.python.org/dev/peps/pep-0526/>`__,
  `ordered dicts <https://stackoverflow.com/a/39980744>`__,
  and :attr:`object.__init_subclass__`.

- Remove the no-longer-needed ``bidict.compat`` module.

- Move :ref:`inverse bidict class access <extending:Dynamic Inverse Class Generation>`
  from a property to an attribute set in
  :attr:`~bidict.BidictBase.__init_subclass__`,
  to save function call overhead on repeated access.

- :meth:`bidict.OrderedBidictBase.__iter__` no longer accepts
  a ``reverse`` keyword argument so that it matches the signature of
  :meth:`container.__iter__`.

- Set the ``__module__`` attribute of various :mod:`bidict` types
  (using :func:`sys._getframe` when necessary)
  so that private, internal modules are not exposed
  e.g. in classes' repr strings.

- :func:`~bidict.namedbidict` now immediately raises :class:`TypeError`
  if the provided ``base_type`` does not provide
  ``_isinv`` or :meth:`~object.__getstate__`,
  rather than succeeding with a class whose instances may raise
  :class:`AttributeError` when these attributes are accessed.


0.20.0 (2020-07-23)
-------------------

The following breaking changes are expected to affect few if any users.

Remove APIs deprecated in the previous release:

- ``bidict.OVERWRITE`` and ``bidict.IGNORE``.

- The ``on_dup_key``, ``on_dup_val``, and ``on_dup_kv`` arguments of
  :meth:`~bidict.bidict.put` and :meth:`~bidict.bidict.putall`.

- The ``on_dup_key``, ``on_dup_val``, and ``on_dup_kv``
  :class:`~bidict.bidict` class attributes.

- Remove :meth:`bidict.BidirectionalMapping.__subclasshook__`
  due to lack of use and maintenance cost.

  Fixes a bug introduced in 0.15.0
  that caused any class with an ``inverse`` attribute
  to be incorrectly considered a subclass of :class:`collections.abc.Mapping`.
  `#111 <https://github.com/jab/bidict/issues/111>`__


0.19.0 (2020-01-09)
-------------------

- Drop support for Python 2
  :ref:`as promised in v0.18.2 <changelog:0.18.2 (2019-09-08)>`.

  The ``bidict.compat`` module has been pruned accordingly.

  This makes bidict more efficient on Python 3
  and enables further improvement to bidict in the future.

- Deprecate ``bidict.OVERWRITE`` and ``bidict.IGNORE``.
  A :class:`UserWarning` will now be emitted if these are used.

  :attr:`bidict.DROP_OLD` and :attr:`bidict.DROP_NEW` should be used instead.

- Rename ``DuplicationPolicy`` to :class:`~bidict.OnDupAction`
  (and implement it via an :class:`~enum.Enum`).

  An :class:`~bidict.OnDupAction` may be one of
  :attr:`~bidict.RAISE`,
  :attr:`~bidict.DROP_OLD`, or
  :attr:`~bidict.DROP_NEW`.

- Expose the new :class:`~bidict.OnDup` class
  to contain the three :class:`~bidict.OnDupAction`\s
  that should be taken upon encountering
  the three kinds of duplication that can occur
  (*key*, *val*, *kv*).

- Provide the
  :attr:`~bidict.ON_DUP_DEFAULT`,
  :attr:`~bidict.ON_DUP_RAISE`, and
  :attr:`~bidict.ON_DUP_DROP_OLD`
  :class:`~bidict.OnDup` convenience instances.

- Deprecate the
  ``on_dup_key``, ``on_dup_val``, and ``on_dup_kv`` arguments
  of :meth:`~bidict.bidict.put` and :meth:`~bidict.bidict.putall`.
  A :class:`UserWarning` will now be emitted if these are used.

  These have been subsumed by the new *on_dup* argument,
  which takes an :class:`~bidict.OnDup` instance.

  Use it like this: ``bi.put(1, 2, OnDup(key=RAISE, val=...))``.
  Or pass one of the instances already provided,
  such as :attr:`~bidict.ON_DUP_DROP_OLD`.
  Or just don't pass an *on_dup* argument
  to use the default value of :attr:`~bidict.ON_DUP_RAISE`.

  The :ref:`basic-usage:Values Must Be Unique` docs
  have been updated accordingly.

- Deprecate the
  ``on_dup_key``, ``on_dup_val``, and ``on_dup_kv``
  :class:`~bidict.bidict` class attributes.
  A :class:`UserWarning` will now be emitted if these are used.

  These have been subsumed by the new
  :attr:`~bidict.bidict.on_dup` class attribute,
  which takes an :class:`~bidict.OnDup` instance.

  See the updated :doc:`extending` docs for example usage.

- Improve the more efficient implementations of
  :meth:`~bidict.BidirectionalMapping.keys`,
  :meth:`~bidict.BidirectionalMapping.values`, and
  :meth:`~bidict.BidirectionalMapping.items`,
  and now also provide a more efficient implementation of
  :meth:`~bidict.BidirectionalMapping.__iter__`
  by delegating to backing :class:`dict`\s
  in the bidict types for which this is possible.

- Move
  :meth:`bidict.BidictBase.values` to
  :meth:`bidict.BidirectionalMapping.values`,
  since the implementation is generic.

- No longer use ``__all__`` in :mod:`bidict`'s ``__init__.py``.


0.18.3 (2019-09-22)
-------------------

- Improve validation of names passed to :func:`~bidict.namedbidict`:
  Use :meth:`str.isidentifier` on Python 3,
  and a better regex on Python 2.

- On Python 3,
  set :attr:`~definition.__qualname__` on :func:`~bidict.namedbidict` classes
  based on the provided ``typename`` argument.


0.18.2 (2019-09-08)
-------------------

- Warn that Python 2 support will be dropped in a future release
  when Python 2 is detected.


0.18.1 (2019-09-03)
-------------------

- Fix a regression introduced by the memory optimizations added in 0.15.0
  which caused
  :func:`deepcopied <copy.deepcopy>` and
  :func:`unpickled <pickle.loads>`
  bidicts to have their inverses set incorrectly.
  `#94 <https://github.com/jab/bidict/issues/94>`__


0.18.0 (2019-02-14)
-------------------

- Rename ``bidict.BidirectionalMapping.inv`` to :attr:`~bidict.BidirectionalMapping.inverse`
  and make :attr:`bidict.BidictBase.inv` an alias for :attr:`~bidict.BidictBase.inverse`.
  `#86 <https://github.com/jab/bidict/issues/86>`__

- :meth:`bidict.BidirectionalMapping.__subclasshook__` now requires an ``inverse`` attribute
  rather than an ``inv`` attribute for a class to qualify as a virtual subclass.
  This breaking change is expected to affect few if any users.

- Add Python 2/3-compatible ``bidict.compat.collections_abc`` alias.

- Stop testing Python 3.4 on CI,
  and warn when Python 3 < 3.5 is detected
  rather than Python 3 < 3.3.

  Python 3.4 reaches `end of life <https://www.python.org/dev/peps/pep-0429/>`__ on 2019-03-18.
  As of January 2019, 3.4 represents only about 3% of bidict downloads on
  `PyPI Stats <https://pypistats.org/packages/bidict>`__.


0.17.5 (2018-11-19)
-------------------

Improvements to performance and delegation logic,
with minor breaking changes to semi-private APIs.

- Remove the ``__delegate__`` instance attribute added in the previous release.
  It was overly general and not worth the cost.

  Instead of checking ``self.__delegate__`` and delegating accordingly
  each time a possibly-delegating method is called,
  revert back to using "delegated-to-fwdm" mixin classes
  (now found in ``bidict._delegating_mixins``),
  and resurrect a mutable bidict parent class that omits the mixins
  as :class:`bidict.MutableBidict`.

- Rename ``__repr_delegate__`` to
  :class:`~bidict.BidictBase._repr_delegate`.


0.17.4 (2018-11-14)
-------------------

Minor code, interop, and (semi-)private API improvements.

- :class:`~bidict.OrderedBidict` optimizations and code improvements.

  Use ``bidict``\s for the backing ``_fwdm`` and ``_invm`` mappings,
  obviating the need to store key and value data in linked list nodes.

- Refactor proxied- (i.e. delegated-) to-``_fwdm`` logic
  for better composability and interoperability.

  Drop the ``_Proxied*`` mixin classes
  and instead move their methods
  into :class:`~bidict.BidictBase`,
  which now checks for an object defined by the
  ``BidictBase.__delegate__`` attribute.
  The ``BidictBase.__delegate__`` object
  will be delegated to if the method is available on it,
  otherwise a default implementation
  (e.g. inherited from :class:`~collections.abc.Mapping`)
  will be used otherwise.
  Subclasses may set ``__delegate__ = None`` to opt out.

  Consolidate ``_MutableBidict`` into :class:`bidict.bidict`
  now that the dropped mixin classes make it unnecessary.

- Change ``__repr_delegate__``
  to simply take a type like :class:`dict` or :class:`list`.

- Upgrade to latest major
  `sortedcontainers <https://github.com/grantjenks/python-sortedcontainers>`__
  version (from v1 to v2)
  for the :ref:`extending:\`\`SortedBidict\`\` Recipes`.

- ``bidict.compat.{view,iter}{keys,values,items}`` on Python 2
  no longer assumes the target object implements these methods,
  as they're not actually part of the
  :class:`~collections.abc.Mapping` interface,
  and provides fallback implementations when the methods are unavailable.
  This allows the :ref:`extending:\`\`SortedBidict\`\` Recipes`
  to continue to work with sortedcontainers v2 on Python 2.


0.17.3 (2018-09-18)
-------------------

- Improve packaging by adding a pyproject.toml
  and by including more supporting files in the distribution.
  `#81 <https://github.com/jab/bidict/pull/81>`__

- Drop pytest-runner and support for running tests via ``python setup.py test``
  in preference to ``pytest`` or ``python -m pytest``.


0.17.2 (2018-04-30)
-------------------

Memory usage improvements
+++++++++++++++++++++++++

- Use less memory in the linked lists that back
  :class:`~bidict.OrderedBidict`\s
  by storing node data unpacked
  rather than in (key, value) tuple objects.


0.17.1 (2018-04-28)
-------------------

Bugfix Release
++++++++++++++

Fix a regression in 0.17.0 that could cause erroneous behavior
when updating items of an :class:`~bidict.Orderedbidict`'s inverse,
e.g. ``some_ordered_bidict.inv[foo] = bar``.


0.17.0 (2018-04-25)
-------------------

Speedups and memory usage improvements
++++++++++++++++++++++++++++++++++++++

- Pass
  :meth:`~bidict.bidict.keys`,
  :meth:`~bidict.bidict.values`, and
  :meth:`~bidict.bidict.items` calls
  (as well as their ``iter*`` and ``view*`` counterparts on Python 2)
  through to the backing ``_fwdm`` and ``_invm`` dicts
  so that they run as fast as possible
  (i.e. at C speed on CPython),
  rather than using the slower implementations
  inherited from :class:`collections.abc.Mapping`.

- Use weakrefs in the linked lists that back
  :class:`~bidict.OrderedBidict`\s
  to avoid creating strong reference cycles.

  Memory for an ordered bidict that you create
  can now be reclaimed in CPython
  as soon as you no longer hold any references to it,
  rather than having to wait until the next garbage collection.
  `#71 <https://github.com/jab/bidict/pull/71>`__


Misc
++++

- Add :attr:`bidict.__version_info__` attribute
  to complement :attr:`bidict.__version__`.


0.16.0 (2018-04-06)
-------------------

Minor code and efficiency improvements to
:func:`~bidict.inverted` and
:func:`~bidict._iter._iteritems_args_kw`
(formerly ``bidict.pairs()``).


Minor Breaking API Changes
++++++++++++++++++++++++++

The following breaking changes are expected to affect few if any users.

- Rename ``bidict.pairs()`` → ``bidict._util._iteritems_args_kw``.


0.15.0 (2018-03-29)
-------------------

Speedups and memory usage improvements
++++++++++++++++++++++++++++++++++++++

- Use :ref:`slots` to speed up bidict attribute access and reduce memory usage.
  On Python 3,
  instantiating a large number of bidicts now uses ~57% the amount of memory
  that it used before,
  and on Python 2 only ~33% the amount of memory that it used before,
  in a simple but representative
  `benchmark <https://github.com/jab/bidict/pull/56#issuecomment-368203591>`__.

- Use weakrefs to refer to a bidict's inverse internally,
  no longer creating a strong reference cycle.
  Memory for a bidict that you create can now be reclaimed
  in CPython as soon as you no longer hold any references to it,
  rather than having to wait for the next garbage collection.
  See the new
  :ref:`addendum:\`\`bidict\`\` Avoids Reference Cycles`
  documentation.
  `#24 <https://github.com/jab/bidict/issues/20>`__

- Make :func:`bidict.BidictBase.__eq__` significantly
  more speed- and memory-efficient when comparing to
  a non-:class:`dict` :class:`~collections.abc.Mapping`.
  (``Mapping.__eq__()``\'s inefficient implementation will now never be used.)
  The implementation is now more reusable as well.

- Make :func:`bidict.OrderedBidictBase.__iter__` as well as
  equality comparison slightly faster for ordered bidicts.

Minor Bugfixes
++++++++++++++

- :func:`~bidict.namedbidict` now verifies that the provided
  ``keyname`` and ``valname`` are distinct,
  raising :class:`ValueError` if they are equal.

- :func:`~bidict.namedbidict` now raises :class:`TypeError`
  if the provided ``base_type``
  is not a :class:`~bidict.BidirectionalMapping`.

- If you create a custom bidict subclass whose ``_fwdm_cls``
  differs from its ``_invm_cls``
  (as in the ``FwdKeySortedBidict`` example
  from the :ref:`extending:\`\`SortedBidict\`\` Recipes`),
  the inverse bidirectional mapping type
  (with ``_fwdm_cls`` and ``_invm_cls`` swapped)
  is now correctly computed and used automatically
  for your custom bidict's
  :attr:`~bidict.BidictBase.inverse` bidict.

Miscellaneous
+++++++++++++

- Classes no longer have to provide an ``__inverted__``
  attribute to be considered virtual subclasses of
  :class:`~bidict.BidirectionalMapping`.

- If :func:`bidict.inverted` is passed
  an object with an ``__inverted__`` attribute,
  it now ensures it is :func:`callable`
  before returning the result of calling it.

- :func:`~bidict.BidictBase.__repr__` no longer checks for a ``__reversed__``
  method to determine whether to use an ordered or unordered-style repr.
  It now calls the new ``__repr_delegate__`` instead
  (which may be overridden if needed), for better composability.

Minor Breaking API Changes
++++++++++++++++++++++++++

The following breaking changes are expected to affect few if any users.

- Split back out the :class:`~bidict.BidictBase` class
  from :class:`~bidict.frozenbidict`
  and :class:`~bidict.OrderedBidictBase`
  from :class:`~bidict.FrozenOrderedBidict`,
  reverting the merging of these in 0.14.0.
  Having e.g. ``issubclass(bidict, frozenbidict) == True`` was confusing,
  so this change restores ``issubclass(bidict, frozenbidict) == False``.

  See the updated :ref:`other-bidict-types:Bidict Types Diagram`
  and :ref:`other-bidict-types:Polymorphism` documentation.

- Rename:

  - ``bidict.BidictBase.fwdm`` → ``._fwdm``
  - ``bidict.BidictBase.invm`` → ``._invm``
  - ``bidict.BidictBase.fwd_cls`` → ``._fwdm_cls``
  - ``bidict.BidictBase.inv_cls`` → ``._invm_cls``
  - ``bidict.BidictBase.isinv`` → ``._isinv``

  Though overriding ``_fwdm_cls`` and ``_invm_cls`` remains supported
  (see :doc:`extending`),
  this is not a common enough use case to warrant public names.
  Most users do not need to know or care about any of these.

- The :attr:`~bidict.RAISE`,
  ``OVERWRITE``, and ``IGNORE``
  duplication policies are no longer available as attributes of
  ``DuplicationPolicy``,
  and can now only be accessed as attributes of
  the :mod:`bidict` module namespace,
  which was the canonical way to refer to them anyway.
  It is now no longer possible to create an infinite chain like
  ``DuplicationPolicy.RAISE.RAISE.RAISE...``

- Make ``bidict.pairs()`` and :func:`bidict.inverted`
  no longer importable from ``bidict.util``,
  and now only importable from the top-level :mod:`bidict` module.
  (``bidict.util`` was renamed ``bidict._util``.)

- Pickling ordered bidicts now requires
  at least version 2 of the pickle protocol.
  If you are using Python 3,
  :attr:`pickle.DEFAULT_PROTOCOL` is 3 anyway,
  so this will not affect you.
  However if you are using in Python 2,
  :attr:`~pickle.DEFAULT_PROTOCOL` is 0,
  so you must now explicitly specify the version
  in your :func:`pickle.dumps` calls,
  e.g. ``pickle.dumps(ob, 2)``.


0.14.2 (2017-12-06)
-------------------

- Make initializing (or updating an empty bidict) from only another
  :class:`~bidict.BidirectionalMapping`
  more efficient by skipping unnecessary duplication checking.

- Fix accidental ignoring of specified ``base_type`` argument
  when (un)pickling a :func:`~bidict.namedbidict`.

- Fix incorrect inversion of
  ``some_named_bidict.inv.<fwdname>_for`` and
  ``some_named_bidict.inv.<invname>_for``.

- Only warn when an unsupported Python version is detected
  (e.g. Python < 2.7) rather than raising :class:`AssertionError`.


0.14.1 (2017-11-28)
-------------------

- Fix a bug introduced in 0.14.0 where hashing a
  :class:`~bidict.frozenbidict`\’s inverse
  (e.g. ``f = frozenbidict(); {f.inv: '...'}``)
  would cause an ``AttributeError``.

- Fix a bug introduced in 0.14.0 for Python 2 users
  where attempting to call ``viewitems()``
  would cause a ``TypeError``.
  `#48 <https://github.com/jab/bidict/issues/48>`__


0.14.0 (2017-11-20)
-------------------

- Fix a bug where :class:`~bidict.bidict`\’s
  default *on_dup_kv* policy was set to :attr:`~bidict.RAISE`,
  rather than matching whatever *on_dup_val* policy was in effect
  as was :ref:`documented <basic-usage:Key and Value Duplication>`.

- Fix a bug that could happen when using Python's optimization (``-O``) flag
  that could leave an ordered bidict in an inconsistent state
  when dealing with duplicated, overwritten keys or values.
  If you do not use optimizations
  (specifically, skipping ``assert`` statements),
  this would not have affected you.

- Fix a bug introduced by the optimizations in 0.13.0 that could cause
  a frozen bidict that compared equal to another mapping
  to have a different hash value from the other mapping,
  violating Python's object model.
  This would only have affected you if you were inserting a
  frozen bidict and some other immutable mapping that it compared equal to
  into the same set or mapping.

- Add :meth:`~bidict.OrderedBidictBase.equals_order_sensitive`.

- Reduce the memory usage of ordered bidicts.

- Make copying of ordered bidicts faster.

- Improvements to tests and CI, including:

  - Test on Windows
  - Test with PyPy3
  - Test with CPython 3.7-dev
  - Test with optimization flags
  - Require pylint to pass


Breaking API Changes
++++++++++++++++++++

This release includes multiple API simplifications and improvements.

- Rename:

  - ``orderedbidict`` → :class:`~bidict.OrderedBidict`
  - ``frozenorderedbidict`` → :class:`~bidict.FrozenOrderedBidict`

  so that these now match the case of :class:`collections.OrderedDict`.

  The names of the
  :class:`~bidict.bidict`,
  :func:`~bidict.namedbidict`, and
  :class:`~bidict.frozenbidict` classes
  have been retained as all-lowercase
  so that they continue to match the case of
  :class:`dict`, :func:`~collections.namedtuple`, and
  :class:`frozenset`, respectively.

- The ``ON_DUP_VAL`` duplication policy value for *on_dup_kv* has been removed.
  Use ``None`` instead.

- Merge :class:`~bidict.frozenbidict` and ``BidictBase``
  together and remove ``BidictBase``.
  :class:`~bidict.frozenbidict`
  is now the concrete base class that all other bidict types derive from.
  See the updated :ref:`other-bidict-types:Bidict Types Diagram`.

- Merge :class:`~bidict.frozenbidict` and ``FrozenBidictBase``
  together and remove ``FrozenBidictBase``.
  See the updated :ref:`other-bidict-types:Bidict Types Diagram`.

- Merge ``frozenorderedbidict`` and ``OrderedBidictBase`` together
  into a single :class:`~bidict.FrozenOrderedBidict`
  class and remove ``OrderedBidictBase``.
  :class:`~bidict.OrderedBidict` now extends
  :class:`~bidict.FrozenOrderedBidict`
  to add mutable behavior.
  See the updated :ref:`other-bidict-types:Bidict Types Diagram`.

- Make :meth:`~bidict.OrderedBidictBase.__eq__`
  always perform an order-insensitive equality test,
  even if the other mapping is ordered.

  Previously,
  :meth:`~bidict.OrderedBidictBase.__eq__`
  was only order-sensitive for other ``OrderedBidictBase`` subclasses,
  and order-insensitive otherwise.

  Use the new :meth:`~bidict.OrderedBidictBase.equals_order_sensitive`
  method for order-sensitive equality comparison.

- ``orderedbidict._should_compare_order_sensitive()`` has been removed.

- ``frozenorderedbidict._HASH_NITEMS_MAX`` has been removed.
  Since its hash value must be computed from all contained items
  (so that hash results are consistent with
  equality comparisons against unordered mappings),
  the number of items that influence the hash value should not be limitable.

- ``frozenbidict._USE_ITEMSVIEW_HASH`` has been removed, and
  ``frozenbidict.compute_hash()``
  now uses ``collections.ItemsView._hash()`` to compute the hash always,
  not just when running on PyPy.

  Override ``frozenbidict.compute_hash()``
  to return ``hash(frozenset(iteritems(self)))``
  if you prefer the old default behavior on CPython,
  which takes linear rather than constant space,
  but which uses the ``frozenset_hash`` routine
  (implemented in ``setobject.c``)
  rather than the pure Python ``ItemsView._hash()`` routine.

- ``loosebidict`` and ``looseorderedbidict`` have been removed.
  A simple recipe to implement equivalents yourself is now given in
  :doc:`extending`.

- Rename ``FrozenBidictBase._compute_hash()`` →
  ``frozenbidict.compute_hash()``.

- Rename ``DuplicationBehavior`` → ``DuplicationPolicy``.

- Rename:

  - ``BidictBase._fwd_class`` → ``.fwd_cls``
  - ``BidictBase._inv_class`` → ``.inv_cls``
  - ``BidictBase._on_dup_key`` → ``on_dup_key``
  - ``BidictBase._on_dup_val`` → ``on_dup_val``
  - ``BidictBase._on_dup_kv`` → ``on_dup_kv``


0.13.1 (2017-03-15)
-------------------

- Fix regression introduced by the new
  :meth:`~bidict.BidirectionalMapping.__subclasshook__`
  functionality in 0.13.0 so that
  ``issubclass(OldStyleClass, BidirectionalMapping)`` once again
  works with old-style classes,
  returning ``False`` rather than raising :class:`AttributeError`
  `#41 <https://github.com/jab/bidict/pull/41>`__


0.13.0 (2017-01-19)
-------------------

- Support Python 3.6.

  (Earlier versions of bidict should work fine on 3.6, but it is officially
  supported starting in this version.)

- :class:`~bidict.BidirectionalMapping`
  has been refactored into an abstract base class,
  following the way :class:`collections.abc.Mapping` works.
  The concrete method implementations it used to provide have been moved
  into a new ``BidictBase`` subclass.

  :class:`~bidict.BidirectionalMapping`
  now also implements
  :meth:`~bidict.BidirectionalMapping.__subclasshook__`,
  so any class that provides a conforming set of attributes
  (enumerated in :attr:`~bidict.BidirectionalMapping._subclsattrs`)
  will be considered a
  :class:`~bidict.BidirectionalMapping`
  subclass automatically.

- ``OrderedBidirectionalMapping`` has been renamed to ``OrderedBidictBase``,
  to better reflect its function. (It is not an ABC.)

- A new ``FrozenBidictBase`` class has been factored out of
  :class:`~bidict.frozenbidict` and
  :class:`frozenorderedbidict <bidict.FrozenOrderedBidict>`.
  This implements common behavior such as caching the result of
  ``__hash__`` after the first call.

- The hash implementations of
  :class:`~bidict.frozenbidict` and
  :class:`frozenorderedbidict <bidict.FrozenOrderedBidict>`.
  have been reworked to improve performance and flexibility.
  :class:`frozenorderedbidict <bidict.FrozenOrderedBidict>`\’s
  hash implementation is now order-sensitive.

  See
  ``frozenbidict._compute_hash()`` and
  ``frozenorderedbidict._compute_hash``
  for more documentation of the changes,
  including the new
  ``frozenbidict._USE_ITEMSVIEW_HASH`` and
  ``frozenorderedbidict._HASH_NITEMS_MAX``
  attributes.
  If you have an interesting use case that requires overriding these,
  or suggestions for an alternative implementation,
  please `share your feedback <https://gitter.im/jab/bidict>`__.

- Add ``_fwd_class`` and ``_inv_class`` attributes
  representing the backing :class:`~collections.abc.Mapping` types
  used internally to store the forward and inverse dictionaries, respectively.

  This allows creating custom bidict types with extended functionality
  simply by overriding these attributes in a subclass.

  See the new :doc:`extending` documentation for examples.

- Pass any parameters passed to :meth:`~bidict.bidict.popitem`
  through to ``_fwd.popitem`` for greater extensibility.

- More concise repr strings for empty bidicts.

  e.g. ``bidict()`` rather than ``bidict({})`` and
  ``orderedbidict()`` rather than ``orderedbidict([])``.

- Add ``bidict.compat.PYPY`` and
  remove unused ``bidict.compat.izip_longest``.

0.12.0 (2016-07-03)
-------------------

- New/renamed exceptions:

  - :class:`~bidict.KeyDuplicationError`
  - :class:`~bidict.ValueDuplicationError`
  - :class:`~bidict.KeyAndValueDuplicationError`
  - :class:`~bidict.DuplicationError` (base class for the above)

- :func:`~bidict.bidict.put`
  now accepts ``on_dup_key``, ``on_dup_val``, and ``on_dup_kv`` keyword args
  which allow you to override the default policy
  when the key or value of a given item
  duplicates any existing item's.
  These can take the following values:

  - :attr:`~bidict.RAISE`
  - ``OVERWRITE``
  - ``IGNORE``

  ``on_dup_kv`` can also take ``ON_DUP_VAL``.

  If not provided,
  :func:`~bidict.bidict.put` uses the
  :attr:`~bidict.RAISE` policy by default.

- New :func:`~bidict.bidict.putall` method
  provides a bulk :func:`~bidict.bidict.put` API,
  allowing you to override the default duplication handling policy
  that :func:`~bidict.bidict.update` uses.

- :func:`~bidict.bidict.update` now fails clean,
  so if an :func:`~bidict.bidict.update` call raises a
  :class:`~bidict.DuplicationError`,
  you can now be sure that none of the given items was inserted.

  Previously, all of the given items that were processed
  before the one causing the failure would have been inserted,
  and no facility was provided to recover
  which items were inserted and which weren't,
  nor to revert any changes made by the failed
  :func:`~bidict.bidict.update` call.
  The new behavior makes it easier to reason about and control
  the effects of failed :func:`~bidict.bidict.update` calls.

  The new :func:`~bidict.bidict.putall` method also fails clean.

  Internally, this is implemented by storing a log of changes
  made while an update is being processed, and rolling back the changes
  when one of them is found to cause an error.
  This required reimplementing :class:`orderedbidict <bidict.OrderedBidict>`
  on top of two dicts and a linked list, rather than two OrderedDicts,
  since :class:`~collections.OrderedDict` does not expose
  its backing linked list.

- :func:`orderedbidict.move_to_end() <bidict.OrderedBidict.move_to_end>`
  now works on Python < 3.2 as a result of the new
  :class:`orderedbidict <bidict.OrderedBidict>` implementation.

- Add

  - ``bidict.compat.viewkeys``
  - ``bidict.compat.viewvalues``
  - ``bidict.compat.iterkeys``
  - ``bidict.compat.itervalues``
  - ``bidict.compat.izip``
  - ``bidict.compat.izip_longest``

  to complement the existing
  ``bidict.compat.iteritems`` and
  ``bidict.compat.viewitems``
  compatibility helpers.

- More efficient implementations of
  ``bidict.pairs()``,
  :func:`~bidict.inverted`, and
  :func:`~bidict.BidictBase.copy`.

- Implement :func:`~bidict.BidictBase.__copy__`
  for use with the :mod:`copy` module.

- Fix issue preventing a client class from inheriting from ``loosebidict``.
  `#34 <https://github.com/jab/bidict/issues/34>`__

- Add benchmarking to tests.

- Drop official support for CPython 3.3.
  (It may continue to work, but is no longer being tested.)

Breaking API Changes
++++++++++++++++++++

- Rename ``KeyExistsException`` → :class:`~bidict.KeyDuplicationError`
  and ``ValueExistsException`` → :class:`~bidict.ValueDuplicationError`.

- When overwriting the key of an existing value in an :class:`orderedbidict <bidict.OrderedBidict>`,
  the position of the existing item is now preserved,
  overwriting the key of the existing item in place,
  rather than moving the item to the end.
  This now matches the behavior of overwriting the value of an existing key,
  which has always preserved the position of the existing item.
  (If inserting an item whose key duplicates that of one existing item
  and whose value duplicates that of another,
  the existing item whose value is duplicated is still dropped,
  and the existing item whose key is duplicated
  still gets its value overwritten in place, as before.)

  For example:

  .. code:: python

     >>> from bidict import orderedbidict  # doctest: +SKIP
     >>> o = orderedbidict([(0, 1), (2, 3)])  # doctest: +SKIP
     >>> o.forceput(4, 1)  # doctest: +SKIP

  previously would have resulted in:

  .. code:: python

     >>> o  # doctest: +SKIP
     orderedbidict([(2, 3), (4, 1)])

  but now results in:

  .. code:: python

     >>> o  # doctest: +SKIP
     orderedbidict([(4, 1), (2, 3)])


0.11.0 (2016-02-05)
-------------------

- Add
  :class:`orderedbidict <bidict.OrderedBidict>`,
  ``looseorderedbidict``, and
  :class:`frozenorderedbidict <bidict.FrozenOrderedBidict>`.

- Add :doc:`code-of-conduct`.

- Drop official support for pypy3.
  (It still may work but is no longer being tested.
  Support may be added back once pypy3 has made more progress.)

0.10.0.post1 (2015-12-23)
-------------------------

- Minor documentation fixes and improvements.


0.10.0 (2015-12-23)
-------------------

- Remove several features in favor of keeping the API simpler
  and the code more maintainable.

- In the interest of protecting data safety more proactively, by default
  bidict now raises an error on attempting to insert a non-unique value,
  rather than allowing its associated key to be silently overwritten.
  See discussion in `#21 <https://github.com/jab/bidict/issues/21>`__.

- New :meth:`~bidict.bidict.forceupdate` method
  provides a bulk :meth:`~bidict.bidict.forceput` operation.

- Fix bugs in
  :attr:`~bidict.bidict.pop` and
  :attr:`~bidict.bidict.setdefault`
  which could leave a bidict in an inconsistent state.

Breaking API Changes
++++++++++++++++++++

- Remove ``bidict.__invert__``, and with it, support for the ``~b`` syntax.
  Use :attr:`~bidict.BidictBase.inv` instead.
  `#19 <https://github.com/jab/bidict/issues/19>`__

- Remove support for the slice syntax.
  Use ``b.inv[val]`` rather than ``b[:val]``.
  `#19 <https://github.com/jab/bidict/issues/19>`__

- Remove ``bidict.invert``.
  Use :attr:`~bidict.BidictBase.inv`
  rather than inverting a bidict in place.
  `#20 <https://github.com/jab/bidict/issues/20>`__

- Raise ``ValueExistsException``
  when attempting to insert a mapping with a non-unique key.
  `#21 <https://github.com/jab/bidict/issues/21>`__

- Rename ``collapsingbidict`` → ``loosebidict``
  now that it suppresses
  ``ValueExistsException``
  rather than the less general ``CollapseException``.
  `#21 <https://github.com/jab/bidict/issues/21>`__

- ``CollapseException`` has been subsumed by
  ``ValueExistsException``.
  `#21 <https://github.com/jab/bidict/issues/21>`__

- :meth:`~bidict.bidict.put` now raises ``KeyExistsException``
  when attempting to insert an already-existing
  key, and ``ValueExistsException`` when
  attempting to insert an already-existing value.


0.9.0.post1 (2015-06-06)
------------------------

- Fix metadata missing in the 0.9.0rc0 release.


0.9.0rc0 (2015-05-30)
---------------------

- Add this changelog,
  `Contributors' Guide <https://github.com/jab/bidict/blob/master/CONTRIBUTING.rst>`__,
  `Gitter chat room <https://gitter.im/jab/bidict>`__,
  and other community-oriented improvements.

- Adopt Pytest.

- Add property-based tests via
  `hypothesis <https://hypothesis.readthedocs.io>`__.

- Other code, tests, and docs improvements.

Breaking API Changes
++++++++++++++++++++

- Move ``bidict.iteritems()`` and ``bidict.viewitems()``
  to new ``bidict.compat`` module.

- Move :class:`bidict.inverted`
  to new ``bidict.util`` module
  (still available from top-level :mod:`bidict` module as well).

- Move ``bidict.fancy_iteritems()`` → ``bidict.util.pairs()``
  (also available from top level as ``bidict.pairs()``).

- Rename :func:`bidict.namedbidict`\'s ``bidict_type`` argument → ``base_type``.

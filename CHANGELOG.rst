.. Forward declarations for all the custom interpreted text roles that
   Sphinx defines and that are used below. This helps Sphinx-unaware tools
   (e.g. rst2html, PyPI's and GitHub's renderers, etc.).
.. role:: doc
.. role:: ref


Changelog
=========

.. image:: https://img.shields.io/badge/GitHub-sponsor-ff69b4
  :target: https://github.com/sponsors/jab
  :alt: Sponsor


:sup:`If you or your organization depends on bidict,
please consider sponsoring bidict on GitHub.`


.. tip::
   Watch `bidict releases on GitHub <https://github.com/jab/bidict/releases>`__
   to be notified when new versions of bidict are published.
   Click the "Watch" dropdown, choose "Custom", and then choose "Releases".


0.23.0 (not yet released)
-------------------------

Primarily, this release simplifies bidict by removing minor features
that are no longer necessary or that have little to no apparent usage,
and it also includes some minor performance optimizations.
These changes will make it easier to maintain and improve bidict in the future,
including further potential performance optimizations.

It also contains several other improvements.

- Drop support for Python 3.7,
  which reached end of life on 2023-06-27,
  and take advantage of features available in Python 3.8+.

- Remove ``FrozenOrderedBidict`` now that Python 3.7 is no longer supported.
  :class:`~bidict.frozenbidict` now provides everything
  that ``FrozenOrderedBidict`` provided
  (including :class:`reversibility <collections.abc.Reversible>`)
  on all supported Python versions,
  but with less space overhead.

- Remove ``namedbidict`` due to low usage.

- Remove the ``kv`` field of :class:`~bidict.OnDup`
  which specified the :class:`~bidict.OnDupAction` to take
  in the case of :ref:`basic-usage:key and value duplication`.
  The :attr:`~bidict.OnDup.val` field now specifies the action to take
  in the case of
  :ref:`basic-usage:key and value duplication`
  as well as
  :ref:`just value duplication <basic-usage:values must be unique>`.

- Improve type hints for the
  :attr:`~bidict.BidictBase.inv` shortcut alias
  for :attr:`~bidict.BidictBase.inverse`.

- Fix a bug where calls like
  ``bidict(None)``, ``bi.update(False)``, etc.
  would fail to raise a :class:`TypeError`.

- All :meth:`~bidict.bidict.__init__`,
  :meth:`~bidict.bidict.update`,
  and related methods
  now handle `SupportsKeysAndGetItem
  <https://github.com/python/typeshed/blob/3eb9ff/stdlib/_typeshed/__init__.pyi#L128-L131>`__
  objects that are not :class:`~collections.abc.Mapping`\s
  the same way that `MutableMapping.update()
  <https://github.com/python/cpython/blob/v3.11.5/Lib/_collections_abc.py#L943>`__ does,
  before falling back to handling the provided object as an iterable of pairs.

- The :func:`repr` of ordered bidicts now matches that of regular bidicts,
  e.g. ``OrderedBidict({1: 1})`` rather than ``OrderedBidict([(1, 1)])``.

  (Accordingly, the ``bidict.__repr_delegate__`` field has been removed
  now that it's no longer needed.)

  This tracks with the change to :class:`collections.OrderedDict`\'s :func:`repr`
  `in Python 3.12 <https://github.com/python/cpython/pull/101661>`__.

- Test with Python 3.12 in CI.

  Note: Older versions of bidict also support Python 3.12,
  even though they don't explicitly declare support for it.

- Drop use of `Trove classifiers <https://github.com/pypa/trove-classifiers>`__
  that declare support for specific Python versions in package metadata.


0.22.1 (2022-12-31)
-------------------

- Only include the source code in the source distribution.
  This reduces the size of the source distribution
  from ~200kB to ~30kB.

- Fix the return type hint of :func:`bidict.inverted`
  to return an :class:`~collections.abc.Iterator`,
  rather than an :class:`~collections.abc.Iterable`.


0.22.0 (2022-03-23)
-------------------

- Drop support for Python 3.6, which reached end of life on 2021-12-23
  and is no longer supported by pip as of pip version 22.
  Take advantage of this to reduce bidict's maintenance costs.

- Use mypy-appeasing explicit re-exports in ``__init__.py``
  (e.g. ``import x as x``)
  so that mypy no longer gives you an implicit re-export error
  if you run it with ``--no-implicit-reexport`` (or ``--strict``)
  against code that imports from :mod:`bidict`.

- Update the implementations and type annotations of
  :meth:`bidict.BidictBase.keys` and
  :meth:`bidict.BidictBase.values` to make use of the new
  :class:`~bidict.BidictKeysView` type,
  which works a bit better with type checkers.

- Inverse bidict instances are now computed lazily the first time
  the :attr:`~bidict.BidictBase.inverse` attribute is accessed
  rather than being computed eagerly during initialization.
  (A bidict's backing, inverse, one-way mapping
  is still kept in sync eagerly as any mutations are made,
  to preserve key- and value-uniqueness.)

- Optimize initializing a bidict with another bidict.
  In a microbenchmark on Python 3.10,
  this now performs over **2x faster**.

- Optimize updating an empty bidict with another bidict.
  In a microbenchmark on Python 3.10,
  this now performs **60-75% faster**.

- Optimize :meth:`~bidict.BidictBase.copy`.
  In a microbenchmark on Python 3.10,
  this now performs **10-20x faster**.

- Optimize rolling back
  :ref:`failed updates to a bidict <basic-usage:Updates Fail Clean>`
  in the case that the number of items passed to the update call
  can be determined to be larger than the bidict being updated.
  Previously this rollback was O(n) in the number of items passed.
  Now it is O(1), i.e. **unboundedly faster**.

- Optimize :meth:`bidict.BidictBase.__contains__`
  (the method called when you run ``key in mybidict``).
  In a microbenchmark on Python 3.10,
  this now performs over **3-10x faster** in the False case,
  and at least **50% faster** in the True case.

- Optimize :meth:`bidict.BidictBase.__eq__`
  (the method called when you run ``mybidict == other``).
  In a microbenchmark on Python 3.10,
  this now performs **15-25x faster** for ordered bidicts,
  and **7-12x faster** for unordered bidicts.

- Optimize :meth:`~bidict.BidictBase.equals_order_sensitive`.
  In a microbenchmark on Python 3.10,
  this now performs **2x faster** for ordered bidicts
  and **60-90% faster** for unordered bidicts.

- Optimize the
  :class:`~collections.abc.MappingView` objects returned by
  :meth:`bidict.OrderedBidict.keys`,
  :meth:`bidict.OrderedBidict.values`, and
  :meth:`bidict.OrderedBidict.items`
  to delegate to backing ``dict_keys`` and ``dict_items``
  objects if available, which are much faster in CPython.
  For example, in a microbenchmark on Python 3.10,
  ``orderedbi.items() == d.items()``
  now performs **30-50x faster**.

- Fix a bug where
  :meth:`bidict.BidictBase.__eq__` was always returning False
  rather than :obj:`NotImplemented`
  in the case that the argument was not a
  :class:`~collections.abc.Mapping`,
  defeating the argument's own ``__eq__()`` if implemented.
  As a notable example, bidicts now correctly compare equal to
  :obj:`unittest.mock.ANY`.

- :class:`bidict.BidictBase` now adds a ``__reversed__`` implementation
  to subclasses that don't have an overridden implementation
  depending on whether both their backing mappings are
  :class:`~collections.abc.Reversible`.
  Previously, a ``__reversed__`` implementation was only added to
  :class:`~bidict.BidictBase` when ``BidictBase._fwdm_cls`` was
  :class:`~collections.abc.Reversible`.
  So if a :class:`~bidict.BidictBase` subclass set its ``_fwdm_cls``
  to a non-reversible mutable mapping,
  it would also have to manually set its ``__reversed__`` attribute to None
  to override the implementation inherited from :class:`~bidict.BidictBase`.
  This is no longer necessary thanks to bidict's new
  :meth:`object.__init_subclass__` logic.

- The
  :class:`~collections.abc.MappingView` objects
  returned by
  :meth:`bidict.OrderedBidict.keys`,
  :meth:`bidict.OrderedBidict.values`, and
  :meth:`bidict.OrderedBidict.items`
  are now
  :class:`~collections.abc.Reversible`.
  (This was already the case for unordered bidicts
  when running on Python 3.8+.)

- Add support for Python 3.9-style dict merge operators
  (`PEP 584 <https://www.python.org/dev/peps/pep-0584/>`__).

  See `the tests <https://github.com/jab/bidict/blob/main/tests/>`__
  for examples.

- Update docstrings for
  :meth:`bidict.BidictBase.keys`,
  :meth:`bidict.BidictBase.values`, and
  :meth:`bidict.BidictBase.items`
  to include more details.

- ``namedbidict`` now
  exposes the passed-in *keyname* and *valname*
  in the corresponding properties on the generated class.

- ``namedbidict`` now requires *base_type*
  to be a subclass of :class:`~bidict.BidictBase`,
  but no longer requires *base_type* to provide
  an ``_isinv`` attribute,
  which :class:`~bidict.BidictBase` subclasses no longer provide.

- When attempting to pickle a bidict's inverse whose class was
  :ref:`dynamically generated
  <extending:Dynamic Inverse Class Generation>`,
  and no reference to the dynamically-generated class has been stored
  anywhere in :data:`sys.modules` where :mod:`pickle` can find it,
  the pickle call is now more likely to succeed
  rather than failing with a :class:`~pickle.PicklingError`.

- Remove the use of slots from (non-ABC) bidict types.

  This better matches the mapping implementations in Python's standard library,
  and significantly reduces code complexity and maintenance burden.
  The memory savings conferred by using slots are not noticeable
  unless you're creating millions of bidict instances anyway,
  which is an extremely unusual usage pattern.

  Of course, bidicts can still contain millions (or more) items
  (which is not an unusual usage pattern)
  without using any more memory than before these changes.
  Notably, slots are still used in the internal linked list nodes of ordered bidicts
  to save memory, since as many node instances are created as there are items inserted.


0.21.4 (2021-10-23)
-------------------

Explicitly declare support for Python 3.10
as well as some minor internal improvements.


0.21.3 (2021-09-05)
-------------------

- All bidicts now provide the :meth:`~bidict.BidictBase.equals_order_sensitive` method,
  not just :class:`~bidict.OrderedBidict`\s.

  Since support for Python < 3.6 was dropped in v0.21.0,
  :class:`dict`\s provide a deterministic ordering
  on all supported Python versions,
  and as a result, all bidicts do too.
  So now even non-:class:`Ordered <bidict.OrderedBidict>` bidicts
  might as well provide :meth:`~bidict.BidictBase.equals_order_sensitive`.

  See the updated
  :ref:`other-bidict-types:What about order-preserving dicts?` docs for more info.

- Take better advantage of the fact that dicts became
  :class:`reversible <collections.abc.Reversible>` in Python 3.8.

  Specifically, now even non-:class:`Ordered <bidict.OrderedBidict>` bidicts
  provide a :meth:`~bidict.BidictBase.__reversed__` implementation on Python 3.8+
  that calls :func:`reversed` on the backing ``_fwdm`` mapping.

  As a result, if you are using Python 3.8+,
  :class:`~bidict.frozenbidict` now gives you everything that
  ``FrozenOrderedBidict`` gives you,
  but with less space overhead.

- Drop `setuptools_scm <https://github.com/pypa/setuptools_scm>`__
  as a ``setup_requires`` dependency.

- Remove the ``bidict.__version_info__`` attribute.


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
  and ``namedbidict``\s),
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

- ``namedbidict`` now immediately raises :class:`TypeError`
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
  :issue:`111`


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


0.18.4 (2020-11-02)
-------------------

- Backport fix from v0.20.0
  that removes :meth:`bidict.BidirectionalMapping.__subclasshook__`
  due to lack of use and maintenance cost.


0.18.3 (2019-09-22)
-------------------

- Improve validation of names passed to ``namedbidict``:
  Use :meth:`str.isidentifier` on Python 3,
  and a better regex on Python 2.

- On Python 3,
  set :attr:`~definition.__qualname__` on ``namedbidict`` classes
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
  :issue:`94`


0.18.0 (2019-02-14)
-------------------

- Rename ``bidict.BidirectionalMapping.inv`` to :attr:`~bidict.BidirectionalMapping.inverse`
  and make :attr:`bidict.BidictBase.inv` an alias for :attr:`~bidict.BidictBase.inverse`.
  :issue:`86`

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

**Memory usage improvements**

- Use less memory in the linked lists that back
  :class:`~bidict.OrderedBidict`\s
  by storing node data unpacked
  rather than in (key, value) tuple objects.


0.17.1 (2018-04-28)
-------------------

**Bugfix Release**

Fix a regression in 0.17.0 that could cause erroneous behavior
when updating items of an :class:`~bidict.Orderedbidict`'s inverse,
e.g. ``some_ordered_bidict.inv[foo] = bar``.


0.17.0 (2018-04-25)
-------------------

**Speedups and memory usage improvements**

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


**Misc**

- Add ``bidict.__version_info__`` attribute
  to complement :attr:`bidict.__version__`.


0.16.0 (2018-04-06)
-------------------

Minor code and efficiency improvements to
:func:`~bidict.inverted` and
``bidict._iter._iteritems_args_kw``
(formerly ``bidict.pairs()``).


**Minor Breaking API Changes**

The following breaking changes are expected to affect few if any users.

- Rename ``bidict.pairs()`` → ``bidict._iter._iteritems_args_kw``.


0.15.0 (2018-03-29)
-------------------

**Speedups and memory usage improvements**

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
  :issue:`24`

- Make :func:`bidict.BidictBase.__eq__` significantly
  more speed- and memory-efficient when comparing to
  a non-:class:`dict` :class:`~collections.abc.Mapping`.
  (``Mapping.__eq__()``\'s inefficient implementation will now never be used.)
  The implementation is now more reusable as well.

- Make :func:`bidict.OrderedBidictBase.__iter__` as well as
  equality comparison slightly faster for ordered bidicts.

**Minor Bugfixes**

- ``namedbidict`` now verifies that the provided
  ``keyname`` and ``valname`` are distinct,
  raising :class:`ValueError` if they are equal.

- ``namedbidict`` now raises :class:`TypeError`
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

**Misc**

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

**Minor Breaking API Changes**

The following breaking changes are expected to affect few if any users.

- Split back out the :class:`~bidict.BidictBase` class
  from :class:`~bidict.frozenbidict`
  and :class:`~bidict.OrderedBidictBase`
  from ``FrozenOrderedBidict``,
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

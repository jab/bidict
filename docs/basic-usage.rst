Basic Usage
-----------

Let's return to the example from the :doc:`intro`:

.. doctest::

   >>> element_by_symbol = bidict(H='hydrogen')

As we saw, this behaves just like a dict,
but maintains a special
:attr:`~bidict.BidictBase.inverse` attribute
giving access to inverse items:

.. doctest::

   >>> element_by_symbol.inverse
   bidict({'hydrogen': 'H'})
   >>> element_by_symbol.inverse['helium'] = 'He'
   >>> element_by_symbol
   bidict({'H': 'hydrogen', 'He': 'helium'})
   >>> del element_by_symbol.inverse['hydrogen']
   >>> element_by_symbol
   bidict({'He': 'helium'})

Note you can also use
:attr:`~bidict.BidictBase.inv` as a shortcut for
:attr:`~bidict.BidictBase.inverse`:

.. doctest::

   >>> element_by_symbol.inv
   bidict({'helium': 'He'})

Both a :class:`bidict.bidict` and its inverse
support the entire
:class:`collections.abc.MutableMapping` interface:

.. doctest::

   >>> 'C' in element_by_symbol
   False
   >>> element_by_symbol.get('C', 'missing')
   'missing'
   >>> element_by_symbol.pop('He')
   'helium'
   >>> element_by_symbol
   bidict()
   >>> element_by_symbol.update(Hg='mercury')
   >>> element_by_symbol
   bidict({'Hg': 'mercury'})
   >>> 'mercury' in element_by_symbol.inverse
   True
   >>> element_by_symbol.inverse.pop('mercury')
   'Hg'

The inverse is automatically kept up-to-date.
Referencing a :class:`~bidict.bidict`'s inverse
is always a constant-time operation;
the inverse is not computed on demand.


Values Must Be Hashable
+++++++++++++++++++++++

Because you must be able to look up keys by value as well as values by key,
values must also be hashable.

Attempting to insert an unhashable value will result in an error:

.. doctest::

   >>> anagrams_by_alphagram = dict(opt=['opt', 'pot', 'top'])
   >>> bidict(anagrams_by_alphagram)
   Traceback (most recent call last):
   ...
   TypeError: ...

So in this example,
using a tuple or a frozenset instead of a list would do the trick:

.. doctest::

   >>> bidict(opt=('opt', 'pot', 'top'))
   bidict({'opt': ('opt', 'pot', 'top')})


Values Must Be Unique
+++++++++++++++++++++

As we know,
in a bidirectional map,
not only must keys be unique,
but values must be unique as well.
This has immediate implications for :mod:`bidict`'s API.

Consider the following:

.. doctest::

   >>> b = bidict({'one': 1})
   >>> b['two'] = 1  # doctest: +SKIP

What should happen next?

If the bidict allowed this to succeed,
because of the uniqueness-of-values constraint,
it would silently clobber the existing item,
resulting in:

.. doctest::

   >>> b  # doctest: +SKIP
   bidict({'two': 1})

This could result in surprises or problems down the line.

Instead, bidict raises a
:class:`~bidict.ValueDuplicationError`
so you have an opportunity to catch this early
and resolve the conflict before it causes problems later on:

.. doctest::

   >>> b['two'] = 1
   Traceback (most recent call last):
       ...
   bidict.ValueDuplicationError: 1

The purpose of this is to be more in line with the
`Zen of Python <https://www.python.org/dev/peps/pep-0020/>`__,
which advises,

| *Errors should never pass silently.*
| *Unless explicitly silenced.*

So if you really just want to clobber any existing items,
all you have to do is say so explicitly:

.. doctest::

   >>> b.forceput('two', 1)
   >>> b
   bidict({'two': 1})

Similarly, initializations and :meth:`~bidict.MutableBidict.update` calls
that would overwrite the key of an existing value
raise an exception too:

.. doctest::

   >>> bidict({'one': 1, 'uno': 1})
   Traceback (most recent call last):
       ...
   bidict.ValueDuplicationError: 1

   >>> b = bidict({'one': 1})
   >>> b.update({'uno': 1})
   Traceback (most recent call last):
       ...
   bidict.ValueDuplicationError: 1

   >>> b
   bidict({'one': 1})

Setting an existing key to a new value
does *not* cause an error,
and is considered an intentional overwrite
of the value associated with the existing key,
in keeping with dict's behavior:

.. doctest::

   >>> b = bidict({'one': 1})
   >>> b['one'] = 2  # succeeds
   >>> b
   bidict({'one': 2})
   >>> b.update([('one', 3), ('one', 4), ('one', 5)])
   >>> b
   bidict({'one': 5})

In summary,
when attempting to insert an item whose key duplicates an existing item's,
:class:`~bidict.bidict`'s default behavior is to allow the insertion,
overwriting the existing item with the new one.
When attempting to insert an item whose value duplicates an existing item's,
:class:`~bidict.bidict`'s default behavior is to raise.
This design naturally falls out of the behavior of Python's built-in dict,
and protects against unexpected data loss.

One set of alternatives to this behavior is provided by
:meth:`~bidict.MutableBidict.forceput`
(mentioned above)
and :meth:`~bidict.MutableBidict.forceupdate`,
which allow you to explicitly overwrite existing keys and values:

.. doctest::

   >>> b = bidict({'one': 1})
   >>> b.forceput('two', 1)
   >>> b
   bidict({'two': 1})

   >>> b.forceupdate([('three', 1), ('four', 1)])
   >>> b
   bidict({'four': 1})

For even more control,
you can use :meth:`~bidict.MutableBidict.put`
and :meth:`~bidict.MutableBidict.putall`.
These variants allow you to pass
an :class:`~bidict.OnDup` instance
to specify custom :class:`~bidict.OnDupAction`\s
for each type of duplication that can occur.

.. doctest::

   >>> b = bidict({1: 'one'})
   >>> b.put(1, 'uno', OnDup(key=RAISE))
   Traceback (most recent call last):
       ...
   bidict.KeyDuplicationError: 1
   >>> b
   bidict({1: 'one'})

:mod:`bidict` provides the
:attr:`~bidict.ON_DUP_DEFAULT`,
:attr:`~bidict.ON_DUP_RAISE`, and
:attr:`~bidict.ON_DUP_DROP_OLD`
:class:`~bidict.OnDup` instances
for convenience.

If no *on_dup* argument is passed,
:meth:`~bidict.MutableBidict.put` and
:meth:`~bidict.MutableBidict.putall`
will use :attr:`~bidict.ON_DUP_RAISE`,
providing stricter-by-default alternatives to
:meth:`~bidict.MutableBidict.__setitem__`
and
:meth:`~bidict.MutableBidict.update`.
(These defaults complement the looser alternatives
provided by :meth:`~bidict.MutableBidict.forceput`
and :meth:`~bidict.MutableBidict.forceupdate`.)


Key and Value Duplication
+++++++++++++++++++++++++

Note that it's possible for a given item to duplicate
the key of one existing item,
and the value of another existing item.

For example:

.. code-block:: python

   b.putall([(1, -1), (2, -2), (1, -2)], on_dup=OnDup(...))

Here, the third item we're trying to insert, (1, -2),
duplicates the key of the first item we're passing, (1, -1),
and the value of the second item we're passing, (2, -2).

Keep in mind, the :class:`~bidict.OnDup`
may specify one :class:`~bidict.OnDupAction`
for :attr:`key duplication <bidict.OnDup.key>`
and a different :class:`~bidict.OnDupAction`
for :attr:`value duplication <bidict.OnDup.val>`.

In the case of a key and value duplication,
the :class:`~bidict.OnDupAction`
for :attr:`value duplication <bidict.OnDup.val>`
takes precedence:

.. doctest::

   >>> on_dup = OnDup(key=DROP_OLD, val=RAISE)
   >>> b.putall([(1, -1), (2, -2), (1, -2)], on_dup=on_dup)
   Traceback (most recent call last):
       ...
   bidict.KeyAndValueDuplicationError: (1, -2)

Note that repeated insertions of the same item
are construed as a no-op and will not raise,
no matter what :class:`~bidict.OnDup` is:

.. doctest::

   >>> b = bidict({1: 'one'})
   >>> b.put(1, 'one')  # no-op, not a DuplicationError
   >>> b.putall([(2, 'two'), (2, 'two')])  # The repeat (2, 'two') is also a no-op.
   >>> b
   bidict({1: 'one', 2: 'two'})

See the :ref:`extending:\`\`YoloBidict\`\` Recipe`
for another way to customize this behavior.


Collapsing Overwrites
+++++++++++++++++++++

When setting an item whose key duplicates that of an existing item,
and whose value duplicates that of a *different* existing item,
the existing item whose *value* is duplicated will be dropped,
and the existing item whose *key* is duplicated
will have its value overwritten in place:

.. doctest::

   >>> b = bidict({1: -1, 2: -2, 3: -3, 4: -4})
   >>> b.forceput(2, -4)  # item with duplicated value, namely (4, -4), is dropped
   >>> b  # and the item with duplicated key, (2, -2), is updated in place:
   bidict({1: -1, 2: -4, 3: -3})
   >>> # (2, -4) took the place of (2, -2), not (4, -4)

   >>> # Another example:
   >>> b = bidict({1: -1, 2: -2, 3: -3, 4: -4})  # as before
   >>> b.forceput(3, -1)
   >>> b
   bidict({2: -2, 3: -1, 4: -4})
   >>> # (3, -1) took the place of (3, -3), not (1, -1)


Updates Fail Clean
++++++++++++++++++

If an update to a :class:`~bidict.bidict` fails,
you can be sure that it fails clean.
In other words, a :class:`~bidict.bidict` will never
apply only part of an update that ultimately fails,
without restoring itself to the state it was in
before processing the update:

.. doctest::

   >>> b = bidict({1: 'one', 2: 'two'})
   >>> b.putall({3: 'three', 1: 'uno'})
   Traceback (most recent call last):
       ...
   bidict.KeyDuplicationError: 1

   >>> # (1, 'uno') was the problem...
   >>> b  # ...but (3, 'three') was not added either:
   bidict({1: 'one', 2: 'two'})


Order Matters
+++++++++++++

Performing a bulk insert operation –
i.e. passing multiple items to
:meth:`~bidict.BidictBase.__init__`,
:meth:`~bidict.MutableBidict.update`,
:meth:`~bidict.MutableBidict.forceupdate`,
or :meth:`~bidict.MutableBidict.putall` –
is like inserting each of those items individually in sequence.
[#fn-fail-clean]_

Therefore, the order of the items provided to the bulk insert operation
is significant to the result.

For example, let's try calling `~bidict.MutableBidict.forceupdate`
with a list of three items that duplicate some keys and values
already in an initial bidict:

.. doctest::

   >>> b = bidict({0: 0, 1: 2})
   >>> b.forceupdate({
   ...     2: 0,     # (2, 0) overwrites (0, 0)            -> bidict({2: 0, 1: 2})
   ...     0: 1,     # (0, 1) is added                     -> bidict({2: 0, 1: 2, 0: 1})
   ...     0: 0,     # (0, 0) overwrites (0, 1) and (2, 0) -> bidict({1: 2, 0: 0})
   ... })
   >>> b
   bidict({1: 2, 0: 0})

Now let's do the exact same thing, but with a different order
of the items that we pass to :meth:`~bidict.MutableBidict.forceupdate`:

.. doctest::

   >>> b = bidict({0: 0, 1: 2})  # as above
   >>> b.forceupdate({
   ...     # same items as above, different order:
   ...     0: 1,     # (0, 1) overwrites (0, 0)            -> bidict({0: 1, 1: 2})
   ...     0: 0,     # (0, 0) overwrites (0, 1)            -> bidict({0: 0, 1: 2})
   ...     2: 0,     # (2, 0) overwrites (0, 0)            -> bidict({1: 2, 2: 0})
   ... })
   >>> b  # different items!
   bidict({1: 2, 2: 0})

Of course, if you try to initialize or update a bidict
with an iterable that yields items in a nondeterministic order,
the results will vary accordingly.

.. [#fn-fail-clean]

   Albeit with the extremely important advantage of
   :ref:`failing clean <basic-usage:Updates Fail Clean>`.


Interop
+++++++

:class:`~bidict.bidict`\s interoperate well with other types of mappings.
For example, they support efficient polymorphic equality testing:

.. doctest::

   >>> bidict(a=1) == dict(a=1)
   True

And converting back and forth works as expected:

.. doctest::

   >>> dict(bidict(a=1))
   {'a': 1}
   >>> bidict(dict(a=1))
   bidict({'a': 1})

(Just remember that if there were any
:ref:`duplicate values <basic-usage:Values Must Be Unique>`
in the dict passed to :class:`~bidict.bidict`,
it would trigger a :class:`~bidict.ValueDuplicationError`.)

See the :ref:`other-bidict-types:Polymorphism` section
for more interoperability documentation.

----

Proceed to :doc:`other-bidict-types`
for documentation on the remaining bidict variants.

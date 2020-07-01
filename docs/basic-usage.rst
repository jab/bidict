Basic Usage
-----------

Let's return to the example from the :doc:`intro`:

.. testsetup::

   from bidict import bidict

.. doctest::

   >>> element_by_symbol = bidict(H='hydrogen')

As we saw, this behaves just like a dict,
but maintains a special
:attr:`~bidict.BidictBase.inverse` attribute
giving access to inverse items:

.. doctest::

   >>> element_by_symbol.inverse['helium'] = 'He'
   >>> del element_by_symbol.inverse['hydrogen']
   >>> element_by_symbol
   bidict({'He': 'helium'})

:class:`bidict.bidict` supports the rest of the
:class:`collections.abc.MutableMapping` interface
as well:

.. doctest::

   >>> 'C' in element_by_symbol
   False
   >>> element_by_symbol.get('C', 'carbon')
   'carbon'
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

Because inverse items are maintained alongside forward items,
referencing a :class:`~bidict.bidict`'s inverse
is always a constant-time operation.


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
   ValueDuplicationError: 1

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

Similarly, initializations and :meth:`~bidict.bidict.update` calls
that would overwrite the key of an existing value
raise an exception too:

.. doctest::

   >>> bidict({'one': 1, 'uno': 1})
   Traceback (most recent call last):
       ...
   ValueDuplicationError: 1

   >>> b = bidict({'one': 1})
   >>> b.update([('uno', 1)])
   Traceback (most recent call last):
       ...
   ValueDuplicationError: 1

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
   >>> bidict([('one', 1), ('one', 2)])
   bidict({'one': 2})

In summary,
when attempting to insert an item whose key duplicates an existing item's,
:class:`~bidict.bidict`'s default behavior is to allow the insertion,
overwriting the existing item with the new one.
When attempting to insert an item whose value duplicates an existing item's,
:class:`~bidict.bidict`'s default behavior is to raise.
This design naturally falls out of the behavior of Python's built-in dict,
and protects against unexpected data loss.

One set of alternatives to this behavior is provided by
:meth:`~bidict.bidict.forceput`
(mentioned above)
and :meth:`~bidict.bidict.forceupdate`,
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
you can use :meth:`~bidict.bidict.put`
and :meth:`~bidict.bidict.putall`.
These variants allow you to pass
an :class:`~bidict.OnDup` instance
to specify custom :class:`~bidict.OnDupAction`\s
for each type of duplication that can occur.

.. doctest::

   >>> from bidict import OnDup, RAISE

   >>> b = bidict({1: 'one'})
   >>> b.put(1, 'uno', OnDup(key=RAISE))
   Traceback (most recent call last):
       ...
   KeyDuplicationError: 2
   >>> b
   bidict({1: 'one'})

:mod:`bidict` provides the
:attr:`~bidict.ON_DUP_DEFAULT`,
:attr:`~bidict.ON_DUP_RAISE`, and
:attr:`~bidict.ON_DUP_DROP_OLD`
:class:`~bidict.OnDup` instances
for convenience.

If no *on_dup* argument is passed,
:meth:`~bidict.bidict.put` and
:meth:`~bidict.bidict.putall`
will use :attr:`~bidict.ON_DUP_RAISE`,
providing stricter-by-default alternatives to
:meth:`~bidict.bidict.__setitem__`
and
:meth:`~bidict.bidict.update`.
(These defaults complement the looser alternatives
provided by :meth:`~bidict.bidict.forceput`
and :meth:`~bidict.bidict.forceupdate`.)


Key and Value Duplication
~~~~~~~~~~~~~~~~~~~~~~~~~

Note that it's possible for a given item to duplicate
the key of one existing item,
and the value of another existing item.
In the following example,
the key of the third item duplicates the first item's key,
and the value of the third item dulicates the second item's value:

.. code-block:: python

   >>> b.putall([(1, 2), (3, 4), (1, 4)], OnDup(key=...))

What should happen next?

Keep in mind, the active :class:`~bidict.OnDup`
may specify one :class:`~bidict.OnDupAction`
for :attr:`key duplication <bidict.OnDup.key>`
and a different :class:`~bidict.OnDupAction`
for :attr:`value duplication <bidict.OnDup.val>`.

To account for this,
:class:`~bidict.OnDup`
allows you to use its
:attr:`~bidict.OnDup.kv` field
to indicate how you want to handle this case
without ambiguity:

.. doctest::

   >>> from bidict import DROP_OLD
   >>> on_dup = OnDup(key=DROP_OLD, val=RAISE, kv=RAISE)
   >>> b.putall([(1, 2), (3, 4), (1, 4)], on_dup)
   Traceback (most recent call last):
       ...
   KeyAndValueDuplicationError: (1, 4)

If not specified, *kv* defaults to whatever was provided for *val*.

Note that repeated insertions of the same item
are construed as a no-op and will not raise,
no matter what the active :class:`~bidict.OnDup` is:

.. doctest::

   >>> b = bidict({1: 'one'})
   >>> b.put(1, 'one')  # no-op, not a DuplicationError
   >>> b.putall([(2, 'two'), (2, 'two')])  # The repeat (2, 'two') is also a no-op.
   >>> sorted(b.items())
   [(1, 'one'), (2, 'two')]

See the :ref:`extending:\`\`YoloBidict\`\` Recipe`
for another way to customize this behavior.


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
   >>> b.putall([(3, 'three'), (1, 'uno')])
   Traceback (most recent call last):
       ...
   KeyDuplicationError: 1

   >>> # (1, 'uno') was the problem...
   >>> b  # ...but (3, 'three') was not added either:
   bidict({1: 'one', 2: 'two'})


Order Matters
+++++++++++++

Performing a bulk insert operation –
i.e. passing multiple items to
:meth:`~bidict.BidictBase.__init__`,
:meth:`~bidict.bidict.update`,
:meth:`~bidict.bidict.forceupdate`,
or :meth:`~bidict.bidict.putall` –
is like inserting each of those items individually in sequence.
[#fn-fail-clean]_

Therefore, the order of the items provided to the bulk insert operation
is significant to the result:

.. doctest::

   >>> b = bidict({0: 0, 1: 2})
   >>> b.forceupdate([(2, 0), (0, 1), (0, 0)])

   >>> # 1. (2, 0) overwrites (0, 0)             -> bidict({2: 0, 1: 2})
   >>> # 2. (0, 1) is added                      -> bidict({2: 0, 1: 2, 0: 1})
   >>> # 3. (0, 0) overwrites (0, 1) and (2, 0)  -> bidict({0: 0, 1: 2})

   >>> sorted(b.items())
   [(0, 0), (1, 2)]

   >>> b = bidict({0: 0, 1: 2})  # as before
   >>> # Give the same items to forceupdate() but in a different order:
   >>> b.forceupdate([(0, 1), (0, 0), (2, 0)])

   >>> # 1. (0, 1) overwrites (0, 0)             -> bidict({0: 1, 1: 2})
   >>> # 2. (0, 0) overwrites (0, 1)             -> bidict({0: 0, 1: 2})
   >>> # 3. (2, 0) overwrites (0, 0)             -> bidict({1: 2, 2: 0})

   >>> sorted(b.items())  # different items!
   [(1, 2), (2, 0)]


.. [#fn-fail-clean]

   Albeit with the extremely important advantage of
   :ref:`failing clean <basic-usage:Updates Fail Clean>`.


Interop
+++++++

:class:`~bidict.bidict`\s interoperate well with other types of mappings.
For example, they support (efficient) polymorphic equality testing:

.. doctest::

   >>> bidict(a=1) == dict(a=1)
   True

And converting back and forth works as expected
(assuming no :ref:`value duplication <basic-usage:Values Must Be Unique>`):

.. doctest::

   >>> dict(bidict(a=1))
   {'a': 1}
   >>> bidict(dict(a=1))
   bidict({'a': 1})

See the :ref:`other-bidict-types:Polymorphism` section
for more interoperability documentation.

----

Hopefully :mod:`bidict` feels right at home
among the Python built-ins you already know.
Proceed to :doc:`other-bidict-types`
for documentation on the remaining bidict variants.

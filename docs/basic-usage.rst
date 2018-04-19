Basic Usage
-----------

Let's return to the example from the :doc:`intro`:

.. code:: python

   >>> from bidict import bidict
   >>> element_by_symbol = bidict(H='hydrogen')

As we saw, this behaves just like a dict,
but maintains a special
:attr:`~bidict.BidictBase.inv` attribute
giving access to inverse items:

.. code:: python

   >>> element_by_symbol.inv['helium'] = 'He'
   >>> del element_by_symbol.inv['hydrogen']
   >>> element_by_symbol
   bidict({'He': 'helium'})

:class:`bidict.bidict` supports the rest of the
:class:`collections.abc.MutableMapping` interface
as well:

.. code:: python

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
   >>> 'mercury' in element_by_symbol.inv
   True
   >>> element_by_symbol.inv.pop('mercury')
   'Hg'

Because inverse items are maintained alongside forward items,
referencing a bidict's inverse
is always a constant-time operation.


Values Must Be Hashable
+++++++++++++++++++++++

Because you must be able to look up keys by value as well as values by key,
values must also be hashable.

Attempting to insert an unhashable value will result in an error:

.. code:: python

   >>> anagrams_by_alphagram = dict(opt=['opt', 'pot', 'top'])
   >>> from bidict import bidict
   >>> bidict(anagrams_by_alphagram)
   Traceback (most recent call last):
   ...
   TypeError: ...

So in this example,
using a tuple or a frozenset instead of a list would do the trick:

.. code:: python

   >>> bidict(opt=('opt', 'pot', 'top'))
   bidict({'opt': ('opt', 'pot', 'top')})


Values Must Be Unique
+++++++++++++++++++++

As we know,
in a bidirectional map,
not only must keys be unique,
but values must be unique as well.
This has immediate implications for bidict's API.

Consider the following:

.. code:: python

   >>> from bidict import bidict
   >>> b = bidict({'one': 1})
   >>> b['two'] = 1  # doctest: +SKIP

What should happen next?

If the bidict allowed this to succeed,
because of the uniqueness-of-values constraint,
it would silently clobber the existing item,
resulting in:

.. code:: python

   >>> b  # doctest: +SKIP
   bidict({'two': 1})

This could result in surprises or problems down the line.

Instead, bidict raises a
:class:`~bidict.ValueDuplicationError`
so you have an opportunity to catch this early
and resolve the conflict before it causes problems later on:

.. code:: python

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
all you have to do is say so:

.. code:: python

   >>> b.forceput('two', 1)
   >>> b
   bidict({'two': 1})

Similarly, initializations and :func:`~bidict.bidict.update` calls
that would overwrite the key of an existing value
raise an exception too:

.. code:: python

   >>> bidict({'one': 1, 'uno': 1})
   Traceback (most recent call last):
       ...
   ValueDuplicationError: 1
   >>> b = bidict({'one': 1})
   >>> b.update([('two', 2), ('uno', 1)])
   Traceback (most recent call last):
       ...
   ValueDuplicationError: 1

If an :func:`~bidict.bidict.update` call raises,
you can be sure that none of the supplied items were inserted:

.. code:: python

   >>> b
   bidict({'one': 1})

Setting an existing key to a new value
does *not* cause an error,
and is considered an intentional overwrite
of the value associated with the existing key,
in keeping with dict's behavior:

.. code:: python

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
bidict's default behavior is to allow the insertion,
overwriting the existing item with the new one.
When attempting to insert an item whose value duplicates an existing item's,
bidict's default behavior is to raise.
This design naturally falls out of the behavior of Python's built-in dict,
and protects against unexpected data loss.

One set of alternatives to this behavior is provided by
:func:`~bidict.bidict.forceput`
(mentioned above)
and :func:`~bidict.bidict.forceupdate`,
which allow you to explicitly overwrite existing keys and values:

.. code:: python

   >>> b = bidict({'one': 1})
   >>> b.forceput('two', 1)
   >>> b
   bidict({'two': 1})

   >>> b.forceupdate([('three', 1), ('four', 1)])
   >>> b
   bidict({'four': 1})

For even more control,
you can use :func:`~bidict.bidict.put`
instead of :func:`~bidict.bidict.forceput`
or :func:`~bidict.bidict.__setitem__`,
and :func:`~bidict.bidict.putall`
instead of :func:`~bidict.bidict.update`
or :func:`~bidict.bidict.forceupdate`.
These methods allow you to specify different strategies for handling
key and value duplication via
the *on_dup_key*, *on_dup_val*, and *on_dup_kv* arguments.
Three possible options are
:attr:`~bidict.RAISE`,
:attr:`~bidict.OVERWRITE`, and
:attr:`~bidict.IGNORE`:

.. code:: python

   >>> from bidict import RAISE, OVERWRITE, IGNORE

   >>> b = bidict({2: 4})
   >>> b.put(2, 8, on_dup_key=RAISE)
   Traceback (most recent call last):
       ...
   KeyDuplicationError: 2
   >>> b
   bidict({2: 4})

   >>> b.putall([(3, 9), (2, 8)], on_dup_key=RAISE)
   Traceback (most recent call last):
       ...
   KeyDuplicationError: 2

   >>> # (2, 8) was the duplicative item, but note that
   >>> # (3, 9) was not added either because the whole call failed:
   >>> b
   bidict({2: 4})

   >>> b.putall([(3, 9), (1, 4)], on_dup_val=IGNORE)
   >>> sorted(b.items())  # Note (1, 4) was ignored as requested:
   [(2, 4), (3, 9)]

If not specified,
the *on_dup_key* and *on_dup_val* keyword arguments of
:func:`~bidict.bidict.put`
and
:func:`~bidict.bidict.putall`
default to
:attr:`~bidict.RAISE`,
providing stricter-by-default alternatives to
:func:`~bidict.bidict.__setitem__`
and
:func:`~bidict.bidict.update`.
(These defaults complement the looser alternatives
provided by :func:`~bidict.bidict.forceput`
and :func:`~bidict.bidict.forceupdate`.)


Key and Value Duplication
~~~~~~~~~~~~~~~~~~~~~~~~~

Note that it's possible for a given item to duplicate
the key of one existing item,
and the value of another existing item, as in:

.. code:: python

   >>> b.putall([(4, 16), (5, 25), (4, 25)])  # doctest: +SKIP

Because the *on_dup_key* and *on_dup_val* policies that are in effect may differ,
*on_dup_kv* allows you to indicate how you want to handle this case
without ambiguity:

.. code:: python

   >>> b.putall([(4, 16), (5, 25), (4, 25)],
   ...          on_dup_key=IGNORE, on_dup_val=IGNORE, on_dup_kv=RAISE)
   Traceback (most recent call last):
       ...
   KeyAndValueDuplicationError: (4, 25)

If not specified, *on_dup_kv* defaults to ``None``,
which causes *on_dup_kv* to match whatever *on_dup_val* policy is in effect.

Note that if an entire *(k, v)* item is duplicated exactly,
the duplicate item will just be ignored,
no matter what the duplication policies are set to.
The insertion of an entire duplicate item is construed as a no-op:

.. code:: python

   >>> sorted(b.items())
   [(2, 4), (3, 9)]
   >>> b.put(2, 4)  # no-op, not a DuplicationError
   >>> b.putall([(4, 16), (4, 16)])  # ditto
   >>> sorted(b.items())
   [(2, 4), (3, 9), (4, 16)]

See the :ref:`extending:OverwritingBidict Recipe`
for another way to customize this behavior.


Order Matters
+++++++++++++

Performing a bulk insert operation –
i.e. passing multiple items to
:meth:`~bidict.BidictBase.__init__`,
:func:`~bidict.bidict.update`,
:func:`~bidict.bidict.forceupdate`,
or :func:`~bidict.bidict.putall` –
is like inserting each of those items individually in sequence.
[#fn-fail-clean]_

Therefore, the order of the items provided to the bulk insert operation
may affect the result:

.. code:: python

   >>> from bidict import bidict
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

   Albeit with an extremely important advantage:
   bulk insertion *fails clean*.
   i.e. If a bulk insertion fails,
   it will leave the bidict in the same state it was before,
   with none of the provided items inserted.


Interop
+++++++

bidicts interoperate well with other types of mappings.
For example, they support (efficient) polymorphic equality testing:

.. code:: python

   >>> from bidict import bidict
   >>> bidict(a=1) == dict(a=1)
   True

And converting back and forth works as expected
(modulo any value duplication, as discussed above):

.. code:: python

   >>> dict(bidict(a=1))
   {'a': 1}
   >>> bidict(dict(a=1))
   bidict({'a': 1})

See the :ref:`other-bidict-types:Polymorphism` section
for more interoperability documentation.


Hopefully bidict feels right at home
among the Python built-ins you already know.
Proceed to :doc:`other-bidict-types`
for documentation on the remaining bidict variants.

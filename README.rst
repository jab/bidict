bidict
======

Efficient, Pythonic bidirectional map implementation and related functionality.

.. image:: ./_static/logo.png
   :target: https://bidict.readthedocs.io/
   :alt: bidict logo


Status
------

.. Hide until https://github.com/badges/shields/issues/716 is fixed
   .. image:: https://img.shields.io/pypi/dm/bidict.svg
      :target: https://pypi.python.org/pypi/bidict
      :alt: Downloads per month

.. image:: https://img.shields.io/pypi/v/bidict.svg
   :target: https://pypi.python.org/pypi/bidict
   :alt: Latest release

.. image:: https://img.shields.io/readthedocs/bidict/master.svg
   :target: https://bidict.readthedocs.io/en/master/
   :alt: Documentation

.. image:: https://api.travis-ci.org/jab/bidict.svg?branch=master
   :target: https://travis-ci.org/jab/bidict
   :alt: Travis-CI build status

.. image:: https://ci.appveyor.com/api/projects/status/gk133415udncwto3/branch/master?svg=true
   :target: https://ci.appveyor.com/project/jab/bidict
   :alt: AppVeyor (Windows) build status

.. image:: https://codecov.io/gh/jab/bidict/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/jab/bidict
   :alt: Test coverage

.. image:: https://api.codacy.com/project/badge/Grade/6628756a73254cd895656348236833b8
   :target: https://www.codacy.com/app/jab/bidict
   :alt: Codacy grade

.. Hide to reduce clutter
   .. image:: https://img.shields.io/pypi/pyversions/bidict.svg
      :target: https://pypi.python.org/pypi/bidict
      :alt: Supported Python versions
   .. image:: https://img.shields.io/pypi/implementation/bidict.svg
      :target: https://pypi.python.org/pypi/bidict
      :alt: Supported Python implementations
   .. image:: https://img.shields.io/badge/lgtm-👍-blue.svg
      :target: https://lgtm.com/projects/g/jab/bidict/
      :alt: LGTM

.. image:: https://img.shields.io/pypi/l/bidict.svg
   :target: https://raw.githubusercontent.com/jab/bidict/master/LICENSE
   :alt: License


Bidict:
^^^^^^^

- is in use by several teams at Google, Venmo, CERN, Bank of America Merrill Lynch,
  Two Sigma, and many others,
- has carefully designed APIs for
  safety, simplicity, flexibility, and ergonomics,
- is CPython-, PyPy-, Python 2-, and Python 3-compatible,
- has extensive `test coverage <https://codecov.io/gh/jab/bidict>`_,
  including property-based tests and benchmarks,
  which are run continuously on all supported Python versions and OSes,
- integrates with Python’s collections interfaces and abstract base classes,
- has mature, well-factored, well-documented code.


Installation
------------

``pip install bidict``


Quick Start
-----------

.. code:: python

   >>> from bidict import bidict
   >>> element_by_symbol = bidict({'H': 'hydrogen'})
   >>> element_by_symbol['H']
   'hydrogen'
   >>> element_by_symbol.inv['hydrogen']
   'H'


For more usage documentation,
head to the :doc:`intro` [#fn-intro]_
and proceed from there.


Community and Support
---------------------

.. image:: https://img.shields.io/badge/chat-on%20gitter-5AB999.svg?logo=gitter-white
   :target: https://gitter.im/jab/bidict
   :alt: Chat

If you are thinking of using bidict in your work,
or if you have any questions, comments, or suggestions,
I'd love to know about your use case
and provide as much support for it as possible.

Please feel free to leave a message in the
`chatroom <https://gitter.im/jab/bidict>`_
or to open a new issue on GitHub.
You can search through
`existing issues <https://github.com/jab/bidict/issues>`_
before creating a new one
in case your questions or concerns have been adressed there already.


Notice of Usage
---------------

If you use bidict,
and especially if your usage or your organization is significant in some way,
please let me know.

You can:

- quickly +1 `this issue <https://github.com/jab/bidict/issues/62>`_
- create your own `dedicated issue <https://github.com/jab/bidict/issues/new?title=Notice+of+Usage&body=I+am+using+bidict+for...>`_
- leave a message in the `chat room <https://gitter.im/jab/bidict>`_
- `email me <mailto:jab@math.brown.edu?subject=bidict&body=I%20am%20using%20bidict%20for...>`_


Changelog
---------

See the :doc:`changelog` [#fn-changelog]_
for a history of notable changes to bidict.


Release Notifications
---------------------

.. duplicated in CHANGELOG.rst:
   (would use `.. include::` but GitHub doesn't understand it)

.. image:: https://img.shields.io/badge/libraries.io-subscribe-5BC0DF.svg
   :target: https://libraries.io/pypi/bidict
   :alt: Follow on libraries.io

Tip: `Subscribe to bidict releases <https://libraries.io/pypi/bidict>`_
on libraries.io to be notified when new versions of bidict are released.


Learning from bidict
--------------------

One of the most rewarding things about bidict
is the outsized amount of advanced Python
it covers in light of its small codebase.

Check out :doc:`learning-from-bidict` [#fn-learning]_
if you're interested in learning more.


Contributing
------------

Bidict is currently a one-person operation
maintained on a voluntary basis
with no other sponsorship.
Your help would be most welcome!


Reviewers Wanted!
^^^^^^^^^^^^^^^^^

One of the most valuable ways to contribute to bidict
and to :doc:`explore some advanced Python <learning-from-bidict>`
while you're at it
is to review bidict's relatively small codebase.

Please create an issue or pull request with any improvements you'd propose
or any other results you found.
(Submitting a "Nothing-to-merge" PR with feedback in inline code comments or a
`Review results <https://github.com/jab/bidict/issues/new?title=Review+results>`_
issue both work well.)

.. The __ in `this issue <...>`__ below is to avoid the warning Sphinx emits
   ("Duplicate explicit target name")
   caused by the other `this issue <...>`_ link above. See:
   https://github.com/sphinx-doc/sphinx/issues/3921#issuecomment-315581557

You can also
+1 `this issue <https://github.com/jab/bidict/issues/63>`__
to sign up to give feedback on future proposed changes
that are in need of a reviewer.


Funding
^^^^^^^

.. duplicated in CONTRIBUTING.rst
   (would use `.. include::` but GitHub doesn't understand it)

If bidict has helped you accomplish your work,
especially work you've been paid for,
please consider chipping in toward the costs
of bidict's maintenance and development
and/or ask your organization to do the same.
Any amount contributed is gratefully received.

.. image:: https://raw.githubusercontent.com/jab/bidict/master/_static/support-on-gumroad.png
   :target: https://gumroad.com/l/bidict
   :alt: Support bidict


Finding Documentation
---------------------

If you're viewing this on `<https://bidict.readthedocs.io>`_,
note that multiple versions of the documentation are available,
and you can choose a different version using the popup menu at the bottom-right.
Please make sure you're viewing the version of the documentation
that corresponds to the version of bidict you'd like to use.

If you're viewing this on GitHub, PyPI, or some other place
that can't render and link this documentation properly
and are seeing broken links,
try these alternate links instead:

.. [#fn-intro] `<docs/intro.rst>`_ | `<https://bidict.readthedocs.io/intro.html>`_

.. [#fn-changelog] `<CHANGELOG.rst>`_ | `<https://bidict.readthedocs.io/changelog.html>`_

.. [#fn-learning] `<docs/learning-from-bidict.rst>`_ | `<https://bidict.readthedocs.io/learning-from-bidict.html>`_


----

Next: :doc:`intro`

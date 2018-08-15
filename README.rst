.. Forward declarations for all the custom interpreted text roles that
   Sphinx defines and that are used below. This helps Sphinx-unaware tools
   (e.g. rst2html, PyPI's and GitHub's renderers, etc.).
.. role:: doc


bidict
======

Efficient, Pythonic bidirectional map implementation and related functionality.

.. image:: https://raw.githubusercontent.com/jab/bidict/master/assets/logo.png
   :target: https://bidict.readthedocs.io/
   :alt: bidict logo


Status
------

.. image:: https://img.shields.io/pypi/v/bidict.svg
   :target: https://pypi.org/project/bidict
   :alt: Latest release

.. image:: https://img.shields.io/readthedocs/bidict/master.svg
   :target: https://bidict.readthedocs.io/en/master/
   :alt: Documentation

.. image:: https://api.travis-ci.org/jab/bidict.svg?branch=master
   :target: https://travis-ci.org/jab/bidict
   :alt: Travis-CI build status

.. image:: https://codecov.io/gh/jab/bidict/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/jab/bidict
   :alt: Test coverage

.. image:: https://img.shields.io/lgtm/alerts/g/jab/bidict.svg
  :target: https://lgtm.com/projects/g/jab/bidict/
  :alt: LGTM alerts

.. image:: https://api.codacy.com/project/badge/Grade/6628756a73254cd895656348236833b8
   :target: https://www.codacy.com/app/jab/bidict
   :alt: Codacy grade

.. Hide to reduce clutter
   .. image:: https://ci.appveyor.com/api/projects/status/gk133415udncwto3/branch/master?svg=true
      :target: https://ci.appveyor.com/project/jab/bidict
      :alt: AppVeyor (Windows) build status
   .. image:: https://img.shields.io/pypi/pyversions/bidict.svg
      :target: https://pypi.org/project/bidict
      :alt: Supported Python versions
   .. image:: https://img.shields.io/pypi/implementation/bidict.svg
      :target: https://pypi.org/project/bidict
      :alt: Supported Python implementations

.. image:: https://img.shields.io/pypi/l/bidict.svg
   :target: https://raw.githubusercontent.com/jab/bidict/master/LICENSE
   :alt: License

.. image:: https://img.shields.io/badge/dynamic/json.svg?label=downloads&url=https%3A%2F%2Fpypistats.org%2Fapi%2Fpackages%2Fbidict%2Frecent%3Fperiod%3Dmonth&query=%24.data.last_month&colorB=blue&suffix=%2fmonth
   :target: https://pypistats.org/packages/bidict
   :alt: Downloads past month


Bidict:
^^^^^^^

- is in use by several teams at Google, Venmo, CERN, Bank of America Merrill Lynch,
  Two Sigma, and many others,
- has carefully designed APIs for
  safety, simplicity, flexibility, and ergonomics,
- is CPython-, PyPy-, Python 2-, and Python 3-compatible,
- has extensive `test coverage <https://codecov.io/gh/jab/bidict>`__,
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
`chatroom <https://gitter.im/jab/bidict>`__
or to open a new issue on GitHub.
You can search through
`existing issues <https://github.com/jab/bidict/issues>`__
before creating a new one
in case your questions or concerns have been adressed there already.


Notice of Usage
---------------

If you use bidict,
and especially if your usage or your organization is significant in some way,
please let me know.

You can:

- `star bidict on GitHub <https://github.com/jab/bidict>`__ (the "star" button is at the top-right)
- `create an issue <https://github.com/jab/bidict/issues/new?title=Notice+of+Usage&body=I+am+using+bidict+for...>`__ (preferred)
- leave a message in the `chat room <https://gitter.im/jab/bidict>`__
- `email me <mailto:jab@math.brown.edu?subject=bidict&body=I%20am%20using%20bidict%20for...>`__


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

Tip: `Subscribe to bidict releases <https://libraries.io/pypi/bidict>`__
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
and to explore some advanced Python [#fn-learning]_
while you're at it
is to review bidict's relatively small codebase.

Please create an issue or pull request with any improvements you'd propose
or any other results you found.
(Submitting a "Nothing-to-merge" PR with feedback in inline code comments or a
`Review results <https://github.com/jab/bidict/issues/new?title=Review+results>`__
issue both work well.)

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

.. image:: https://raw.githubusercontent.com/jab/bidict/master/assets/support-on-gumroad.png
   :target: https://gumroad.com/l/bidict
   :alt: Support bidict


Finding Documentation
---------------------

If you're viewing this on `<https://bidict.readthedocs.io>`__,
note that multiple versions of the documentation are available,
and you can choose a different version using the popup menu at the bottom-right.
Please make sure you're viewing the version of the documentation
that corresponds to the version of bidict you'd like to use.

If you're viewing this on GitHub, PyPI, or some other place
that can't render and link this documentation properly
and are seeing broken links,
try these alternate links instead:

.. [#fn-intro] `<docs/intro.rst>`__ | `<https://bidict.readthedocs.io/intro.html>`__

.. [#fn-changelog] `<CHANGELOG.rst>`__ | `<https://bidict.readthedocs.io/changelog.html>`__

.. [#fn-learning] `<docs/learning-from-bidict.rst>`__ | `<https://bidict.readthedocs.io/learning-from-bidict.html>`__


----

Next: :doc:`intro` [#fn-intro]_

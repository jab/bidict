.. Forward declarations for all the custom interpreted text roles that
   Sphinx defines and that are used below. This helps Sphinx-unaware tools
   (e.g. rst2html, PyPI's and GitHub's renderers, etc.).
.. role:: doc

.. Use :doc: rather than :ref: references below for better interop as well.


bidict
======

The bidirectional mapping library for Python.

.. image:: https://raw.githubusercontent.com/jab/bidict/main/assets/logo-sm-white-bg.jpg
   :target: https://bidict.readthedocs.io/
   :alt: bidict logo


Status
------

.. image:: https://img.shields.io/pypi/v/bidict.svg
   :target: https://pypi.org/project/bidict
   :alt: Latest release

.. image:: https://img.shields.io/readthedocs/bidict/main.svg
   :target: https://bidict.readthedocs.io/en/main/
   :alt: Documentation

.. image:: https://github.com/jab/bidict/workflows/Tests/badge.svg
   :target: https://github.com/jab/bidict/actions
   :alt: GitHub Actions CI status

.. image:: https://codecov.io/gh/jab/bidict/branch/main/graph/badge.svg
   :target: https://codecov.io/gh/jab/bidict
   :alt: Test coverage

.. Hide to reduce clutter
   .. image:: https://img.shields.io/lgtm/alerts/github/jab/bidict.svg
      :target: https://lgtm.com/projects/g/jab/bidict/
      :alt: LGTM alerts
   .. image:: https://bestpractices.coreinfrastructure.org/projects/2354/badge
      :target: https://bestpractices.coreinfrastructure.org/en/projects/2354
      :alt: CII best practices badge
   .. image:: https://img.shields.io/badge/tidelift-pro%20support-orange.svg
      :target: https://tidelift.com/subscription/pkg/pypi-bidict?utm_source=pypi-bidict&utm_medium=referral&utm_campaign=docs
      :alt: Paid support available via Tidelift
   .. image:: https://img.shields.io/pypi/pyversions/bidict.svg
      :target: https://pypi.org/project/bidict
      :alt: Supported Python versions
   .. image:: https://img.shields.io/pypi/implementation/bidict.svg
      :target: https://pypi.org/project/bidict
      :alt: Supported Python implementations

.. image:: https://img.shields.io/pypi/l/bidict.svg
   :target: https://raw.githubusercontent.com/jab/bidict/main/LICENSE
   :alt: License

.. image:: https://static.pepy.tech/badge/bidict
   :target: https://pepy.tech/project/bidict
   :alt: PyPI Downloads

.. image:: https://img.shields.io/badge/GitHub-sponsor-ff69b4
  :target: https://github.com/sponsors/jab
  :alt: Sponsor through GitHub


bidict:
^^^^^^^

- has been used for many years by several teams at
  **Google, Venmo, CERN, Bank of America Merrill Lynch, Bloomberg, Two Sigma,** and many others
- has carefully designed APIs for
  **safety, simplicity, flexibility, and ergonomics**
- is **fast, lightweight, and has no runtime dependencies** other than Python's standard library
- **integrates natively** with Python’s ``collections.abc`` interfaces
- provides **type hints** for all public APIs
- is implemented in **concise, well-factored, pure (PyPy-compatible) Python code**
  that is **optimized for running efficiently**
  as well as for **reading and learning** [#fn-learning]_
- has **extensive docs and test coverage**
  (including property-based tests and benchmarks)
  run continuously on all supported Python versions


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
   >>> element_by_symbol.inverse['hydrogen']
   'H'


For more usage documentation,
head to the :doc:`intro` [#fn-intro]_
and proceed from there.


Voluntary Community Support
---------------------------

.. image:: https://img.shields.io/badge/gitter-chat-5AB999.svg?logo=gitter-white
   :target: https://gitter.im/jab/bidict
   :alt: Chat

Please feel free to leave a message in the
`bidict chatroom <https://gitter.im/jab/bidict>`__
or open a new issue on GitHub
for voluntary community support.
You can search through
`existing issues <https://github.com/jab/bidict/issues>`__
before creating a new one
in case your issue has been addressed already.


Enterprise Support
------------------

.. image:: https://img.shields.io/badge/tidelift-enterprise%20support-orange.svg
   :target: https://tidelift.com/subscription/pkg/pypi-bidict?utm_source=pypi-bidict&utm_medium=referral&utm_campaign=readme
   :alt: Enterprise support via Tidelift

Enterprise-level support for bidict can be obtained via the
`Tidelift subscription <https://tidelift.com/subscription/pkg/pypi-bidict?utm_source=pypi-bidict&utm_medium=referral&utm_campaign=readme>`__.


Notice of Usage
---------------

If you use bidict,
and especially if your usage or your organization is significant in some way,
please let me know in any of the following ways:

- `star bidict on GitHub <https://github.com/jab/bidict>`__
- `create an issue <https://github.com/jab/bidict/issues/new?title=Notice+of+Usage&body=I+am+using+bidict+for...>`__
- leave a message in the `chat room <https://gitter.im/jab/bidict>`__
- `email me <mailto:jabronson@gmail.com?subject=bidict&body=I%20am%20using%20bidict%20for...>`__


Changelog
---------

See the :doc:`changelog` [#fn-changelog]_
for a history of notable changes to bidict.


Release Notifications
---------------------

.. duplicated in CHANGELOG.rst:
   (would use `.. include::` but GitHub doesn't understand it)

Watch releases
`on GitHub <https://github.blog/changelog/2018-11-27-watch-releases/>`__
to be notified when new versions of bidict are released.


Learning from bidict
--------------------

One of the best things about bidict
is that it touches a surprising number of
interesting Python corners,
especially given its small size and scope.

Check out :doc:`learning-from-bidict` [#fn-learning]_
if you're interested in learning more.


Contributing
------------

bidict is currently a one-person operation
maintained on a voluntary basis.

Your help would be most welcome!
See the :doc:`contributors-guide` [#fn-contributing]_
for more information.


Sponsoring
^^^^^^^^^^

.. duplicated in CONTRIBUTING.rst
   (would use `.. include::` but GitHub doesn't understand it)

.. image:: https://img.shields.io/badge/GitHub-sponsor-ff69b4
  :target: https://github.com/sponsors/jab
  :alt: Sponsor through GitHub

Bidict is the product of thousands of hours of my unpaid work
over the 12+ years I've been maintaining it.

If bidict has helped you accomplish your work,
especially work you've been paid for,
it's easy to
`sponsor me through GitHub <https://github.com/sponsors/jab>`__.

Choose a tier and GitHub handles everything else.
The sponsorship just goes on your regular GitHub bill;
there's nothing extra to do.
You can also sponsor me through
`Gumroad <https://gumroad.com/l/bidict>`__ or
`PayPal <https://www.paypal.com/cgi-bin/webscr?cmd=_xclick&business=jabronson%40gmail%2ecom&lc=US&item_name=Sponsor%20bidict%20(name%20a%20fair%20price)>`__.

Read more about
`companies supporting open source developers
<https://www.cognitect.com/blog/supporting-open-source-developers>`__.


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

.. [#fn-learning] `<docs/learning-from-bidict.rst>`__ | `<https://bidict.readthedocs.io/learning-from-bidict.html>`__

.. [#fn-changelog] `<CHANGELOG.rst>`__ | `<https://bidict.readthedocs.io/changelog.html>`__

.. [#fn-intro] `<docs/intro.rst>`__ | `<https://bidict.readthedocs.io/intro.html>`__

.. [#fn-contributing] `<docs/contributors-guide.rst>`__ | `<https://bidict.readthedocs.io/contributors-guide.html>`__


----

Next: :doc:`intro` [#fn-intro]_

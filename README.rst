bidict
======

Efficient, Pythonic bidirectional map implementation and related functionality.

.. image:: ./_static/logo.png
    :target: https://bidict.readthedocs.io/
    :alt: bidict logo


Status
------

.. Hide until https://github.com/badges/shields/issues/716 is fixed
.. .. image:: https://img.shields.io/pypi/dm/bidict.svg
..     :target: https://pypi.python.org/pypi/bidict
..     :alt: Downloads per month

.. image:: https://img.shields.io/pypi/v/bidict.svg
    :target: https://pypi.python.org/pypi/bidict
    :alt: Latest release

.. image:: https://img.shields.io/readthedocs/bidict/master.svg
    :target: https://bidict.readthedocs.io/en/master/
    :alt: Documentation

.. image:: https://travis-ci.org/jab/bidict.svg?branch=master
    :target: https://travis-ci.org/jab/bidict
    :alt: Travis-CI build status (Linux and macOS)

.. image:: https://ci.appveyor.com/api/projects/status/gk133415udncwto3/branch/master?svg=true
    :target: https://ci.appveyor.com/project/jab/bidict
    :alt: AppVeyor build status (Windows)

.. image:: https://coveralls.io/repos/jab/bidict/badge.svg?branch=master
    :target: https://coveralls.io/github/jab/bidict
    :alt: Test coverage

.. Hide to reduce clutter
.. .. image:: https://img.shields.io/pypi/pyversions/bidict.svg
..     :target: https://pypi.python.org/pypi/bidict
..     :alt: Supported Python versions
..
.. .. image:: https://img.shields.io/pypi/implementation/bidict.svg
..     :target: https://pypi.python.org/pypi/bidict
..     :alt: Supported Python implementations

.. image:: https://img.shields.io/badge/chat-on--gitter-5AB999.svg?logo=gitter-white
    :target: https://gitter.im/jab/bidict
    :alt: Chat

.. image:: https://img.shields.io/badge/Say%20Thanks-😊-1EAEDB.svg
    :target: https://saythanks.io/to/jab
    :alt: Say thanks

.. image:: https://img.shields.io/pypi/l/bidict.svg
    :target: https://raw.githubusercontent.com/jab/bidict/master/LICENSE
    :alt: License


Bidict:
^^^^^^^

- is in use by several teams at Google, Bank of America Merrill Lynch,
  and many others,
- has carefully designed APIs for
  safety, ergonomics, performance, and intuitiveness,
- is CPython-, PyPy-, Python 2-, and Python 3-compatible,
- has extensive `test coverage <https://coveralls.io/github/jab/bidict>`_,
  including property-based tests and benchmarks,
  which are run continuously on all supported Python versions and OSes,
- integrates with Python’s collections interfaces and abstract base classes,
- is thoroughly and attentively documented,
  and
- is made up of mature, concise, and well-reviewed code.

If you are thinking of using bidict in your work,
or if you have any questions, comments, or suggestions,
I'd love to know about your use case
and provide as much support for it as possible.

If you are already using bidict and especially if
you/your organization is a significant user,
please `let me know <https://saythanks.io/to/jab>`_ you're using it!

Please feel free to leave a message in the
`chatroom <https://gitter.im/jab/bidict>`_
or `open an issue <https://github.com/jab/bidict/issues>`_
after reviewing the :doc:`contributors-guide`. [#fn-contributing]_


Changelog
---------

For a history of notable changes to bidict,
check out the :doc:`changelog`. [#fn-changelog]_


.. .. include:: release-notifications.rst.inc
.. duplicate rather than `include` release-notifications so it renders on GitHub:

Release Notifications
---------------------

.. image:: https://img.shields.io/badge/Sibbell-follow-brightgreen.svg
    :target: https://sibbell.com/github/jab/bidict/releases/
    :alt: Follow on Sibbell


Tip: `Follow bidict on Sibbell <https://sibbell.com/github/jab/bidict/releases/>`_
to be notified when a new version of bidict is released.


Installation
------------

``pip install bidict``


Usage Documentation
-------------------

For usage documentation, please start at the :doc:`intro`
and proceed from there.

.. NOTE::
   If you're reading this on GitHub, PyPI, in your code editor,
   or in some other place that can't render/link the full docs properly,
   you can find the bidict documentation on Read the Docs at:

       `<https://bidict.readthedocs.io>`_

   Also note: multiple versions of the documentation are published on Read the Docs,
   and by default you will be taken to the version built from the master branch.
   You can choose different versions from the pop-up menu in the lower-right.

   If you have the `bidict source code <https://github.com/jab/bidict>`_  handy,
   you can also browse the docs inside the ``docs`` directory,
   and build them yourself by running ``make html`` from within that directory
   (requires `Sphinx <https://pypi.python.org/pypi/Sphinx>`_).


Contributing
------------

Bidict is currently a one-person operation
maintained on a voluntary basis for the public good.
Your help would be most welcome.

If bidict has helped you accomplish your work,
especially work you've been paid for,
please consider supporting bidict's maintenance and development.

.. image:: https://raw.githubusercontent.com/jab/bidict/master/_static/support-on-gumroad.png
    :target: https://gumroad.com/l/bidict
    :alt: Support bidict

For information about contributing to the code,
please see the :doc:`contributors-guide`. [#fn-contributing]_


Alternate Links
---------------

In case you're viewing on GitHub, PyPI,
or some other place that can't render/link the full docs properly:

.. [#fn-contributing] `<CONTRIBUTING.rst>`_ | `<https://bidict.readthedocs.io/contributors-guide.html>`_

.. [#fn-changelog] `<CHANGELOG.rst>`_ | `<https://bidict.readthedocs.io/changelog.html>`_

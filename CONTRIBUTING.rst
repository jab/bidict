.. Forward declarations for all the custom interpreted text roles that
   Sphinx defines and that are used below. This helps Sphinx-unaware tools
   (e.g. rst2html, PyPI's and GitHub's renderers, etc.).
.. role:: doc
.. role:: ref


Contributors' Guide
===================

Bug reports, feature requests, patches, and other contributions are warmly welcomed.
Contribution should be as easy and friendly as possible.
Below are a few guidelines contributors should follow to facilitate the process.


Getting Started
---------------

- `Create a GitHub account <https://github.com/join>`__ if you don't have one
  already.

- Search through the `issue tracker <https://github.com/jab/bidict/issues>`__
  to see if an issue or pull request has already been created for what you're interested in.
  If so, feel free to add comments to it or just hit the "subscribe" button to follow progress.
  If not, you can `join the chat room <https://gitter.im/jab/bidict>`__ to discuss there,
  or go ahead and `create a new issue <https://github.com/jab/bidict/issues/new>`__:

  - Clearly describe the issue giving as much relevant context as possible.

  - If it is a bug, include reproduction steps,
    all known environments in which the bug is exhibited,
    and ideally a failing test case.

- If you would like to contribute a patch,
  make sure you've `created your own fork <https://github.com/jab/bidict/fork>`__
  and have cloned it to your computer.


Making Changes
--------------

- Before making changes, please
  (create a `virtualenv <http://virtualenv.pypa.io>`__ and)
  install the extra packages required for development:
  ``pip install -r requirements/dev.txt``

  We use `EditorConfig <https://editorconfig.org/>`__
  and `pre-commit <https://pre-commit.com/>`__
  to help achieve uniform style and quality standards
  across a diversity of development environments.

  pre-commit gets installed when you run the command above
  and ensures that various code checks are run before every commit
  (look in ``.pre-commit-config.yaml`` to see which hooks are run).
  Ensure the configured hooks are installed by running
  ``pre-commit install --install-hooks``.

  EditorConfig allows us to provide a single ``.editorconfig`` file
  to configure settings like indentation consistently
  across a variety of supported editors.
  See https://editorconfig.org/#download to install the plugin for your editor.

- Create a topic branch off of master for your changes:
  ``git checkout -b <topic> master``

- Make commits of logical units.

- Match the existing code style and quality standards.
  If you're adding a feature, include accompanying tests and documentation
  demonstrating its correctness and usage.

- Run the tests locally with `tox <https://tox.readthedocs.io>`__
  to make sure they pass for all supported Python versions
  (see ``envlist`` in ``tox.ini`` for the complete list).
  If you do not have all the referenced Python versions available locally,
  you can also push the changes on your branch to GitHub
  to automatically trigger a new
  `GitHub Actions <https://github.com/jab/bidict/actions>`__ build,
  which should run the tests for all supported Python versions.

- Create a concise but comprehensive commit message in the following style::

    Include an example commit message in CONTRIBUTING guide #9999

    Without this patch the CONTRIBUTING guide would contain no examples of
    a model commit message. This is a problem because the contributor is left
    to imagine what the commit message should look like and may not get it
    right. This patch fixes the problem by providing a concrete example.

    The first line is an imperative statement summarizing the changes with an
    issue number from the tracker. The body describes the behavior without
    the patch, why it's a problem, and how the patch fixes the problem.


Submitting Changes
------------------

- Push your changes to a topic branch in your fork of the repository:
  ``git push --set-upstream origin <topic>``

- Submit a pull request providing any additional relevant details necessary.

- Acknowledgment should typically be fast
  but please allow 1-2 weeks for a full response / code review.

- The code review process often involves some back-and-forth
  to get everything right before merging.
  This is typical of quality software projects that accept patches.

- All communication should be supportive and appreciative of good faith efforts to contribute,
  creating a welcoming and inclusive community.
  Expect nothing less of any project.


Sponsoring
----------

.. image:: https://img.shields.io/badge/GitHub-sponsor-ff69b4
  :target: https://github.com/sponsors/jab
  :alt: Sponsor through GitHub

.. image:: https://img.shields.io/badge/Gumroad-sponsor-55a0a4.svg
  :target: https://gumroad.com/l/bidict
  :alt: Sponsor through Gumroad

.. image:: https://img.shields.io/badge/PayPal-sponsor-blue.svg
  :target: https://www.paypal.com/cgi-bin/webscr?cmd=_xclick&business=jabronson%40gmail%2ecom&lc=US&item_name=Sponsor%20bidict%20(name%20a%20fair%20price)
  :alt: Sponsor through PayPal

.. duplicated in README.rst
   (would use `.. include::` but GitHub doesn't understand it)

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


Code of Conduct
---------------

All participation in this project should respect the
:doc:`code-of-conduct`. [#fn-coc]_

By participating, you are expected to honor this code.

.. [#fn-let-me-know] `<https://bidict.readthedocs.io/#notice-of-usage>`__
.. [#fn-coc] `<CODE_OF_CONDUCT.rst>`_ | `<https://bidict.readthedocs.io/code-of-conduct.html>`__

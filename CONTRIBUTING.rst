.. _contributors-guide:

Contributors' Guide
===================

Bug reports, feature requests, patches, and other contributions are warmly welcomed.
Contribution should be as easy and friendly as possible.
Below are a few guidelines contributors should follow to facilitate the process.

Getting Started
---------------

- `Create a GitHub account <https://github.com/join>`_ if you don't have one
  already.

- Search through the `issue tracker <https://github.com/jab/bidict/issues>`_
  to see if an issue or pull request has already been created for what you're interested in.
  If so, feel free to add comments to it or just hit the "subscribe" button to follow progress.
  If not, you can `join the chat room <https://gitter.im/jab/bidict>`_ to discuss there,
  or go ahead and `create a new issue <https://github.com/jab/bidict/issues/new>`_:

  - Clearly describe the issue giving as much relevant context as possible.

  - If it is a bug, include reproduction steps,
    all known environments in which the bug is exhibited,
    and ideally a failing test case.

- If you would like to contribute a patch,
  make sure you've `created your own fork <https://github.com/jab/bidict/fork>`_
  and have cloned it to your computer.

Making Changes
--------------

- Before making changes, please install the extra packages required for development:
  ``pip install -e .[dev]``

  We use `EditorConfig <http://editorconfig.org/>`_
  and `pre-commit <http://pre-commit.com/>`_
  to help achieve uniform style and quality standards
  across a diversity of development environments.

  pre-commit gets installed when you run ``pip install -e .[dev]``
  and ensures that various code checks are run before every commit
  (look in ``.pre-commit-config.yaml`` to see which hooks are run).

  EditorConfig allows us to provide a single ``.editorconfig`` file
  to configure settings like indentation consistently
  across a variety of suppored editors.
  See http://editorconfig.org/#download to install the plugin for your editor.

- Create a topic branch off of master for your changes:
  ``git checkout -b <topic> master``

- Make commits of logical units.

- Match the existing code style and quality standards.
  If you're adding a feature, include accompanying tests and documentation
  demonstrating its correctness and usage.

- Run the tests locally with `tox <https://tox.readthedocs.io>`_
  to make sure they pass for all supported Python versions
  (see ``envlist`` in ``tox.ini`` for the complete list).
  If you do not have all the referenced Python versions available locally,
  you can also push the changes on your branch to GitHub
  to automatically trigger a new `Travis-CI <https://travis-ci.org>`_ build,
  which should run the tests for all supported Python versions.
  You should be able to see the results at ``travis-ci.org/<user>/bidict``,
  where ``<user>`` is the GitHub username you used to fork bidict.

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

Becoming a Core Contributor
---------------------------

Currently `@jab <https://github.com/jab>`_ is the only person responsible
for bidict maintenance and development.
Additional core contributors are welcome.

Donation and Other Ways to Contribute
-------------------------------------

Besides filing issues and pull requests, there are other ways to contribute.

.. image:: https://img.shields.io/badge/Gumroad-Support%20bidict-orange.svg
  :target: https://gumroad.com/l/bidict
  :alt: Gumroad - Support bidict

.. image:: https://img.shields.io/badge/Bountysource-Support%20bidict-brightgreen.svg
  :target: https://www.bountysource.com/teams/bidict
  :alt: Bountysource - Support bidict

.. image:: https://img.shields.io/badge/PayPal-Support%20bidict-blue.svg
  :target: https://www.paypal.com/cgi-bin/webscr?cmd=_xclick&business=jab%40math%2ebrown%2eedu&lc=US&item_name=Support%20bidict&button_subtype=services&currency_code=USD&bn=PP%2dBuyNowBF%3aPaypal%2dBuy%2520a%2520Drink%2dblue%2esvg%3aNonHosted
  :alt: PayPal - Support bidict

- If you read the code and learned something new,
  let us know and it'll give us the warm fuzzies.

- If you're using bidict in a project you work on, blog about your experience.

- If you come across other people who could find it useful, spread the word.

- If bidict has helped you accomplish your work,
  especially work you've been paid for,
  please `support bidict's continued maintenance and development
  <https://gumroad.com/l/bidict>`_
  and/or ask your organization to do the same.

.. image:: ./_static/support-on-gumroad.png
  :target: https://gumroad.com/l/bidict
  :alt: Support bidict

Code of Conduct
---------------

All participation in this project should respect the
:doc:`code-of-conduct`. [#fn-coc]_

By participating, you are expected to honor this code.

Thanks
------

Contributions are gratefully received.
Thank you for your friendly participation.

.. [#fn-coc] `<CODE_OF_CONDUCT.rst>`_ | `<https://bidict.readthedocs.io/code-of-conduct.html>`_

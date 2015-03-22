Contributors' Guide
===================

Bug reports, feature requests, patches, and other contributions are more than welcome.
We want to make contribution as easy and friendly as possible.
Here are a few guidelines we ask contributors to follow to facilitate the process:

Getting Started
---------------

- Make sure you have a `GitHub account <https://github.com/join>`_.

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
  and have cloned it to your machine.

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

- Run all the tests
  with `tox <https://tox.readthedocs.org>`_
  to make sure nothing else was accidentally broken.

- Create a concise but comprehensive commit message in the following style::

      #99999 Include an example commit message in CONTRIBUTING guide

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

Currently @jab is the only person responsible for bidict maintenance and development,
and so far all effort put into the project has been made possible only by volunteering free time.
Additional core contributors are more than welcome.
Feel free to ask for the commit bit if you don't have it already.
Frequent contributors will be offered it proactively.

Other Ways to Contribute
------------------------

Besides creating issues and pull requests, there are other ways to contribute.
If you read the code and learned something new, let us know and it'll give us the warm fuzzies.
If you're using bidict in a project you work on, blog about your experience.
If you come across other people who could find it useful, spread the word.
If you or your organization has benefited from bidict commercially or otherwise,
you can use `Bountysource <https://www.bountysource.com/teams/jab>`_
to sponsor a new feature or bugfix, or make a general donation.
You can also use this if it's more your cup of tea:

.. image:: https://img.shields.io/badge/Paypal-Buy%20a%20Drink-blue.svg
    :target: https://www.paypal.com/cgi-bin/webscr?cmd=_xclick&business=jab%40math%2ebrown%2eedu&lc=US&item_name=Buy%20a%20drink%20for%20jab&button_subtype=services&currency_code=USD&bn=PP%2dBuyNowBF%3aPaypal%2dBuy%2520a%2520Drink%2dblue%2esvg%3aNonHosted
    :alt: PayPal - Buy a drink

Thanks
------

Thank you for stopping by. Any contributions gratefully received!

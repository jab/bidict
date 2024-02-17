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

- Search through the `tracker <https://github.com/jab/bidict/issues?q=>`__
  to see if an issue or pull request has already been created for what you're interested in.
  If so, feel free to add comments to it or just hit the "subscribe" button to follow progress.
  If not, you can post in the
  `GitHub Discussions forum <https://github.com/jab/bidict/discussions>`__,
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

- You can work on bidict in a Visual Studio Code
  `devcontainer environment <https://code.visualstudio.com/docs/remote/containers>`__,
  where development dependencies and some helpful VS Code extensions
  are installed inside the dev container environment for you.

  Try ``Remote-Containers: Clone Repository in Container Volume...`` on this
  repository. You may need to reload your VS Code window after it finishes
  cloning and installing extensions, which it should automatically prompt you to do
  when you open your clone in VS Code.

  - Note that `pre-commit <https://pre-commit.com/>`__
    is used to help achieve uniform style and quality standards.

- If not using a VSCode devcontainer, you can try the following
  to set up a development environment manually:

  - If you have `Nix <https://nixos.org>`__, you can run
    ``nix develop`` from within your clone to start a shell
    where all supported Python versions as well as ``pre-commit``
    are installed and added to your PATH.

    Otherwise, manually ensure you have `pre-commit <https://pre-commit.com>`__
    and at least the latest `stable Python version <https://python.org/downloads/>`__
    installed and on your PATH.

  - Run ``./init_dev_env``

    This installs the git hooks for ``pre-commit`` in your clone,
    creates a virtualenv with all the development dependencies installed,
    and reminds you to activate the virtualenv env it just created when ready.

- Create a topic branch off of ``main`` for your changes:
  ``git checkout -b <topic> main``

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
  Testing your changes with GitHub Actions will require approval
  from a project admin the first time you submit a PR.

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


Sponsoring
----------

.. Some of the following badges are duplicated on other pages.
   Would use `.. include::` but GitHub's renderer doesn't support it.

.. image:: https://img.shields.io/badge/GitHub-sponsor-ff69b4
  :target: https://github.com/sponsors/jab
  :alt: Sponsor through GitHub

.. image:: https://img.shields.io/badge/PayPal-sponsor-blue.svg
  :target: https://www.paypal.com/cgi-bin/webscr?cmd=_xclick&business=jabronson%40gmail%2ecom&lc=US&item_name=Sponsor%20bidict
  :alt: Sponsor through PayPal

Bidict is the product of thousands of hours of my unpaid work
over the 15+ years that I've been the sole maintainer.

If bidict has helped you or your company accomplish your work,
please sponsor my work through one of the following,
and/or ask your company to do the same:

- `GitHub <https://github.com/sponsors/jab>`__
- `PayPal <https://www.paypal.com/cgi-bin/webscr?cmd=_xclick&business=jabronson%40gmail%2ecom&lc=US&item_name=Sponsor%20bidict>`__
- `Tidelift <https://tidelift.com>`__
- `thanks.dev <https://thanks.dev>`__
- `Gumroad <https://gumroad.com/l/bidict>`__
- `a support engagement with my LLC <https://bidict.readthedocs.io/#enterprise-support>`__

If you're not sure which to use, GitHub is an easy option,
especially if you already have a GitHub account.
Just choose a monthly or one-time amount, and GitHub handles everything else.
Your bidict sponsorship on GitHub will automatically go
on the same regular bill as any other GitHub charges you pay for.
PayPal is another easy option for one-time contributions.

See the following for rationale and examples of companies
supporting the open source projects they depend on
in this manner:

- `<https://engineering.atspotify.com/2022/04/announcing-the-spotify-foss-fund/>`__
- `<https://blog.sentry.io/2021/10/21/we-just-gave-154-999-dollars-and-89-cents-to-open-source-maintainers>`__
- `<https://engineering.indeedblog.com/blog/2019/07/foss-fund-six-months-in/>`__

.. - `<https://sethmlarson.dev/blog/people-in-your-software-supply-chain>`__
.. - `<https://www.cognitect.com/blog/supporting-open-source-developers>`__
.. - `<https://vorpus.org/blog/the-unreasonable-effectiveness-of-investment-in-open-source-infrastructure/>`__


Code of Conduct
---------------

All participation in this project should respect the
:doc:`code-of-conduct`. [#fn-coc]_

By participating, you are expected to honor this code.

.. [#fn-coc] `<https://bidict.readthedocs.io/code-of-conduct.html>`__ | `<CODE_OF_CONDUCT.rst>`__

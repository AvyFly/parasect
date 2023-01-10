Contributor Guide
=================

Thank you for your interest in improving this project.
This project is open-source under the `MIT license`_ and
welcomes contributions in the form of bug reports, feature requests, and pull requests.

Here is a list of important resources for contributors:

- `Source Code`_
- `Documentation`_
- `Issue Tracker`_
- `Code of Conduct`_

.. _MIT license: https://opensource.org/licenses/MIT
.. _Source Code: https://github.com/AvyFly/parasect
.. _Documentation: https://parasect.readthedocs.io/
.. _Issue Tracker: https://github.com/AvyFly/parasect/issues

How to report a bug
-------------------

Report bugs on the `Issue Tracker`_.

When filing an issue, make sure to answer these questions:

- Which operating system and Python version are you using?
- Which version of this project are you using?
- What did you do?
- What did you expect to see?
- What did you see instead?

The best way to get your bug fixed is to provide a test case,
and/or steps to reproduce the issue.


How to request a feature
------------------------

Request features on the `Issue Tracker`_.


How to set up your development environment
------------------------------------------

First of all, clone the *Parasect* repository.

Then, you need Python 3.8+ and the following tools:

- Poetry_
- Nox_
- nox-poetry_

Install Poetry_ by downloading and running the following script:

.. code:: console

   $ curl -sSL https://install.python-poetry.org | python3 -


Install Nox_ and nox-poetry_:

.. code:: console

   $ pipx install nox
   $ pipx inject nox nox-poetry

Navigate into the location where you cloned *Parasect* and install the package with development requirements:

.. code:: console

   $ poetry install

You can now run an interactive Python session,
or the command-line interface:

.. code:: console

   $ poetry run python
   $ poetry run parasect

.. _Poetry: https://python-poetry.org/
.. _Nox: https://nox.thea.codes/
.. _nox-poetry: https://nox-poetry.readthedocs.io/


How to test the project
-----------------------

The *Parasect* CLI offers debug output in the form of a ``parasect.log`` file.
The file can be created by issuing the ``--debug`` flag when calling *Parasect*.

.. code:: console

   $ parasect --debug <rest_of_the_arguments>

Additionally, you can run the full test suite:

.. code:: console

   $ nox

List the available Nox sessions:

.. code:: console

   $ nox --list-sessions

You can also run a specific Nox session.
For example, invoke the unit test suite like this:

.. code:: console

   $ nox --session=tests

Unit tests are located in the ``tests`` directory,
and are written using the pytest_ testing framework.

.. _pytest: https://pytest.readthedocs.io/


How to submit changes
---------------------

Open a `pull request`_ to submit changes to this project.

Your pull request needs to meet the following guidelines for acceptance:

- The Nox test suite must pass without errors and warnings.
- Include unit tests. You must provide tests covering 100% of your code changes and additions.
- If your changes add functionality, update the documentation accordingly.

Feel free to submit early. Mark your PR as WIP (Work in Progress) in the PR title, to signal that it is not in its final form yet.

To run linting and code formatting checks before committing your change, you can install pre-commit as a Git hook by running the following command:

.. code:: console

   $ nox --session=pre-commit -- install

If you are unsure how your contribution would fit in *Parasect*, feel free to raise an issue for discussion.
It is always preferable to spend a little time discussing your approach, instead of spending a lot of effort on a large chunk of code that might be rejected.

.. _pull request: https://github.com/AvyFly/parasect/pulls
.. github-only
.. _Code of Conduct: CODE_OF_CONDUCT.rst

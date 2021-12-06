.. unikube-cli documentation master file

Welcome to the Unikube CLI Documentation!
=========================================

This is the Unikube CLI reference guide.

This command line interface is implemented using Python and the
`Click framework <https://click.palletsprojects.com/en/7.x/>`_. The CLI is realized with the following goals in mind:

* easy and intuitive for developers
* scriptable (for continuous integration/delivery scenarios)
* portable


Command groups
==============
All Unikube CLI commands are divided into several command groups, which represent a specific concept or unit, such as
:ref:`unikube auth<unikube_auth>`, :ref:`unikube system<unikube_system>` or :ref:`unikube project<unikube_project>`.
However, there are additional :ref:`shortcuts<unikube_shortcut>` for frequently used commands, which are directly
accessible under :program:`unikube`, such as the :ref:`reference/shortcut:login`.

Generally, commands in unikube CLI looks like this:

.. code-block:: shell

   unikube <COMMAND GROUP> <COMMAND> [--OPTION]

.. toctree::
    :glob:

    reference/shortcut
    reference/auth
    reference/orga
    reference/project
    reference/deck
    reference/app
    reference/system
    reference/context

Indices and Tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

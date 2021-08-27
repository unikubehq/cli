=========
Reference
=========
This is the Unikube CLI reference guide.

This command line interface is implemented using Python and the
`Click framework <https://click.palletsprojects.com/en/7.x/>`_. The CLI is realized with the following goals in mind:

* easy and intuitive for developers
* scriptable (for continuous integration/delivery scenarios)
* portable

Context management
==================
Unikube's CLI can manage :ref:`organisations<unikube_orga>`, :ref:`projects<unikube_project>`,
:ref:`decks<unikube_deck>` and interact with :ref:`apps<unikube_app>`. As it can be cumbersome to enter identifiers
again and again, you can set a ``context`` for the commands to implicitly assume a certain unit (pretty much the same as
with ``kubectl``). In order to set a context, run the ``use`` command from the corresponding command groups:
:ref:`unikube organisation use<reference/orga:use>`, :ref:`unikube project use<reference/project:use>` and
:ref:`unikube deck use<reference/deck:use>`.


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

    shortcut
    auth
    orga
    project
    deck
    app
    system


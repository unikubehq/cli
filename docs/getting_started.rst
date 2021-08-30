===============
Getting Started
===============

Unikube is a tool to enable developers to create cloud native applications locally.

Unikube CLI Installation
========================

The Unikube CLI can be installed using :code:`pip`:

.. code-block:: shell

   pip install --upgrade unikube

In order to install the latest pre-release use
:code:`pip`:

.. code-block:: shell

   pip install --upgrade unikube --pre

After the installation has completed, open up a new shell and run :code:`unikube --version` to verify your installation. 
Now you can get started by logging in into your account.

You don't have an Unikube account? Register at `unikube.io <https://app.unikube.io>`__!

**Note**: `python2` is not supported. Therefore, depending on your local python installation, you may need to run :code:`pip3 install unikube`.


Authentication
==============
To authenticate with your Unikube account, run:

.. code-block:: shell

    unikube login

It will redirect you to the login web page. See :ref:`the login reference<reference/auth:login>` for more information.

To log out from your account, run:

.. code-block:: shell

    unikube logout


Local System Preparation
========================
After authentication, verify that your system is prepared for running a Kubernetes cluster locally:

.. code-block:: shell

    unikube system verify

Are you missing dependencies on your local machine?

No Problem! Unikube makes it easy to install many of the required dependencies. Just execute:

.. code-block:: shell

   unikube system install

Now you can run :code:`unikube system verify` again to check if all dependencies have been installed correctly.
See the :ref:`install reference<reference/system:install>` or :ref:`verify reference<reference/system:verify>` for more
information.

Hello Unikube!
==============

Using unikube is as easy as:


.. code-block:: shell

   unikube login
   unikube project up <project>

At this point, your local cluster is up and running! Happy developing!

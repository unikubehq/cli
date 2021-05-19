===============
Getting Started
===============

Unikube is a tool to enable developers to develop cloud native applications locally.

Unikube CLI Installation
========================

The Unikube CLI can be installed using :code:`pip`:

.. code-block:: shell

   pip install unikube

After the installation has completed, open up a new shell and run :code:`unikube --version` to verify your installation. 
Now you can get started by logging in into your account. You don't have an Unikube account? Register at `unikube.io <https://unikube.io>`__!

Please note that `python2` is not supported. Therefore, depending on your local python installation, you may need to run :code:`pip3 install unikube`.


Authentication
==============
Run :code:`unikube login` to authenticate with your Unikube account, or :code:`unikube logout` to log out of your account. 


Local System Preparation
========================
After authentication, verify that your system is prepared for running a Kubernetes cluster locally:

.. code-block:: shell

    unikube system verify

Are you missing dependencies on your local machine? No Problem! Unikube makes it easys to install many of the required dependencies. Just execute:

.. code-block:: shell

   unikube system install

Now you can run :code:`unikube system verify` again to check if all dependencies have been installed correctly.


Hello Unikube!
==============

Using unikube is as easy as:


.. code-block:: shell

   unikube login
   unikube project up hello-unikube

At this point, your local cluster is up and running! Happy developing!

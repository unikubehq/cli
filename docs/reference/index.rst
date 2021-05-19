=========
Reference
=========


All Unikube CLI commands are organized into different groups, such as :ref:`unikube auth<unikube_auth>`, :ref:`unikube system<unikube_system>` or :ref:`unikube project<unikube_project>`. 
However, there are additional shortcuts for frequently used commands, which are directly accessible under :ref:`unikube<unikube_shortcut>`, such as :code:`unikube login`. 
In the following, commands with shortcuts are described first as they cover the main workflow with the Unikube CLI. 
Detailed information about shortcuts can be found in the corresponding group sections. 

.. _unikube_shortcut:

.. click:: unikube:cli
  :prog: unikube
  :commands: login, logout, install
  :nested: short


.. _unikube_auth:

.. click:: unikube:auth
  :prog: unikube auth
  :commands: login, logout, status
  :nested: full


.. _unikube_system:

.. click:: unikube:system
  :prog: unikube system
  :commands: install, verify
  :nested: full


.. _unikube_orga:

.. click:: unikube:orga
  :prog: unikube orga
  :commands: list
  :nested: full


.. _unikube_project:

.. click:: unikube:project
  :prog: unikube project
  :commands: list, up
  :nested: full

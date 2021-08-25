=======================
Developing with Unikube
=======================
Unikube does not simply give you the possibility to setup and run a local Kubernetes cluster. It aims to be an
application development system. Unikube developers are able to write code directly within a Kubernetes environment
without the need to take care of any Kubernetes aspects.

This chapter describes how you can prepare an application development setup to leverage the full convenience of the
Unikube CLI.

Switch operation
================
The command :code:`unikube app switch` (see :ref:`unikube app switch<reference/app:switch>`)  is the central entry point
for local Kubernetes-based development. The idea is to literally *switch* a locally running container with an instance
running in a (Unikube provided) Kubernetes cluster. All network traffic from and to the cluster instance is then
tunneled to the local application. That enables developers to make changes to the source code, files, environment
variables (and other settings) and let them run in the context of all the other attached services.

.. figure:: _static/img/project-unikube-1.png

   After running :code:`unikube deck install` (see :ref:`unikube app switch<reference/deck:install>`) a Kubernetes
   cluster is running all services.

.. figure:: _static/img/project-unikube-2.png

   The command :ref:`unikube app switch<reference/app:switch>` (see :ref:`unikube app switch<reference/app:switch>`)
   starts a local container and tunnels all traffic to the target within the cluster.

You may run the :code:`unikube app switch` command with a long parameter list, or execute the command from a
location containing a `Unikubefile`_.


Unikubefile
===========

The *Unikubefile* is a file with *yaml* notation, that should contain all necessary information for Unikube about
the service. It specifies specify a Docker build, volumes, environment, commands and context. The file must be named
*unikube.yaml* for the command :code:`unikube app switch` to be automatically used.

The `unikube.yaml` schema look like this:


.. code-block:: yaml

    # unikube switch configuration file
    apps:
        projects:
            context: # the CLI context
                organization: <Organization ID>
                project: <Project ID>
                deck: <Deck ID>
            build:
                context: <Path to Docker build root>
                dockerfile: <Path to Dockerfile>
                target: <Dockerfile build target>
        deployment: <Name of the Deployment in the cluster>
        command: <Starting command> # overwrite the run command of the services during development
        volumes:
          - <Path to the volume mounts> # overwrite the container's source directory with your working tree
        env:
          - <Environment variable>:<Value> # overwrite environment variables from the deployment, see: unikube app env

The source repository of the project should include a valid Dockerfile (path to the dockerfile) and a Unikubefile.

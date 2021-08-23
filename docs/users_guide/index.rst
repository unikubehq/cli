============
User's guide
============

Unikube CLI has many convenient commands, that make it much easier to manage unikube.

Unikubefile
===========

Unikubefile is a yaml file, that should have all the necessary information for unikube about the project. It should
specify a docker build, volumes, environment, commands and context.

An example unikube.yaml could look like this:


.. code-block:: yaml

    # unikube switch configuration file
    apps:
      projects:
        build:
          context:
            organization: <Organization ID>
            project: <Project ID>
            deck: <Deck ID>
          dockerfile: <Path to Dockerfile>
        deployment: <Path to Deployment>
        command: <Starting command>
        volumes:
          - <Path to the volume directory>
        env:
          - <Environment variable>:<Value>

Build of the project should include a valid dockerfile (path to the dockerfile) and can include a context, which in
turn could consist of organization, project and deck, any of which should be specified with ID respectively. Command is
a starting command for a container e.g. django manage starting command to start Django application in the docker
container.
Volume should specify a valid path to the directory, where volume should be mounted.
Environment variables can be added in the env section, specified by it's name followed by it's value separated with a
colon.

Command groups
==============
Commands are divided into several command groups, which represent a specific concept or unit. Command group is basically
a generalized term for all the commands it has under the hood. For instance, command group ``unikube auth`` has several
subcommands under the hood, which are all related to user authentication. The main command groups are:

- auth
- system
- orga
- project
- deck
- app

Generally, command in unikube CLI looks like this:

.. code-block:: shell

   unikube <COMMAND GROUP> <COMMAND> [--OPTION]

Auth command group
==================
Auth group includes following subcommands:

- login
- logout
- status

Authentication command group unites all subcommands for managing unikube authentication process. Beside standard ``login``
and ``logout`` commands, you can check your current authentication status by using ``status`` command.
``login`` command redirects user to the login webpage.
If you want to login yourself via CLI without being redirected to the webpage, you can just specify parameters -e for
email and -p for password as in the following command:

.. code-block:: shell

   unikube login -e <EMAIL> -p <PASSWORD>

System command group
====================
System group includes following subcommands:

- install
- verify

This command group includes two very important commands: ``install`` and ``verify``. Using these commands you can install
all necessary dependencies for unikube and verify their versions. Via ``install`` command Docker,
Docker Engine, Kubectl, k3d and Telepresence are installed.

To reinstall dependency use ``--reinstall`` with the ``login`` command. You need to specify name of dependency with the
``--reinstall`` option, as:

.. code-block:: shell

   unikube system install --reinstall Kubectl

``verify`` command can be used with a verbose option to get a tabular view of installed dependencies, their status, version
and a required version.

Orga command group
==================
Orga group includes following subcommands:

- list
- info
- use


Every registered user can belong to one or multiple organizations and can get authorized for the projects of that
organization. Unikube uses a concept of organization as a command group for managing information about organization.
You can list all organizations you belong to by running ``unikube orga list`` command. It presents a tabular view of
organizations with id and name of organization. ``unikube orga info`` command can be used to get more detailed
information about particular organization. This command displays the id, title and an optional description of the
organization. It belongs to the group of selection commands, thus it has three possible options:
1. you can either manually enter the organization_id as an optional positional argument
2. you can have a context already set with organization_id, then the info for the set organization will be displayed
3. if none of the above options is specified, user will be prompted to the selection view of all possible organizations,
that the user belongs to.

Project command group
=====================

Project is a very important command group. It includes following subcommands:

- list
- info
- use
- up
- down
- delete

``unikube project list`` returns a tabular list of all available projects for the user alongside with the IDs.

``unikube project info`` is a selection command and displays the id, title and optional description of the
project.

``unikube project use`` is a context command, it belongs to a group of selection commands and allows to set a project
context.

``unikube project up`` starts a cluster for the specified project. As it is a selection command, project can be specified
in several ways: as a positional argument ID or project title can be specified, as a set context or as a selection from
avalable projects for the user. Projects can also be filtered via ``-o`` or ``--organization`` option, specifying
organization to which they belong. ``--ingress`` option is available for specifying the ingress port of the project.
``-p`` or ``--provider`` is available for setting a Kubernetes provider type for the cluster other than the default
"k3d". ``--workers`` which specifies a number of k3d worker nodes.

``unikube project down`` stops/pauses the current cluster. Project id or title can be specified, otherwise context or
project selection will be performed. Currently, unikube supports only one current cluster at a
time. Login is not necessary for this command.

``unikube project delete`` deletes the current cluster with all related data. Project id or title can be specified,
otherwise context or project selection will be performed. Login is not necessary for this command.

Deck command group
==================
Deck group includes following subcommands:

- list
- info
- use
- install
- uninstall
- ingress

``unikube deck list`` returns a tabular list of all available decks for the user alongside with the IDs.

``unikube deck info`` is a selection command and displays the id, title, description, namespace and a type of the
deck.

``unikube deck use`` is a context command, it belongs to a group of selection commands and allows to set a deck
context.

``unikube deck install`` installing the deck. Deck Id or title can be specified as an optional argument.

``unikube deck uninstall`` uninstalling the deck. Deck Id or title can be specified as an optional argument.

``unikube deck ingress`` displaying the ingress data for the installed deck.


App command group
=================
App group includes following subcommands:

- list
- info
- shell/exec
- switch
- logs
- env

``unikube app list`` returns a tabular list of all apps.

``unikube app info`` displays the status for the given app. Optional arguments
are organization, project and deck.

``unikube app shell``/``unikube app exec`` starts an interactive shell session in the current container. App can be
specified as an argument. Optional arguments are organization, project and deck.

``unikube app switch`` switches a running deployment with a local docker image. App can be
specified as an argument. Optional arguments are organization, project and deck. Additionally, deployment can be
can be specified, if not specified in the unikube file. Path to the unikubefile can also be specified, if not in the
current directory.

``unikube app logs`` displays logs of the container, that can be used for debug purposes. App can be
specified as an argument. Optional arguments are organization, project and deck. Container can be specified via ``-c``
or ``--container``. ``-f`` or ``--follow`` if you want to follow the logs.

``unikube app env`` displays environment variables for the given app name. App can be specified as an argument.
Optional arguments are organization, project and deck. ``-i`` or ``--init``if you want to display environment variables
for the init container.

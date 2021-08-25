============
User's guide
============






Project command group
=====================

Project is a very important command group. It includes following subcommands:

- list
- info
- use
- up
- down
- delete


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

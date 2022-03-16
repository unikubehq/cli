import sys

import click
from click_didyoumean import DYMGroup

import unikube.cli.console as console
from unikube.cli import app as app_cmd
from unikube.cli import auth as auth_cmd
from unikube.cli import context as context_cmd
from unikube.cli import deck as deck_cmd
from unikube.cli import init as init_cmd
from unikube.cli import orga as orga_cmd
from unikube.cli import project as project_cmd
from unikube.cli import system as system_cmd
from unikube.cli import unikube as unikube_cmd
from unikube.completion.completion import render_completion_script
from unikube.context import ClickContext
from unikube.helpers import compare_current_and_latest_versions

version = sys.version_info
if version.major == 2:
    console.error("Python 2 is not supported for Unikube. Please upgrade python.", _exit=True)


@click.group(cls=DYMGroup, max_suggestions=2, cutoff=0.5)
@click.pass_context
def cli(ctx, **kwargs):
    """
    The Unikube CLI provides several command groups to manage all required aspects to develop cloud native
    software on a Kubernetes-based environment.

    There are a couple of shortcut commands directly available from here.
    """
    ctx.obj = ClickContext()


# click -----
@click.command()
def version():
    """
    Check unikube version.
    """
    version = compare_current_and_latest_versions()
    if version is None:
        console.error("Could not determine version.")

    console.info(f"unikube, version {version}")


cli.add_command(version)
cli.add_command(unikube_cmd.ps)


@cli.group(cls=DYMGroup, max_suggestions=2, cutoff=0.5)
@click.pass_obj
def system(ctx):
    """
    The ``system`` command group includes commands to manage system dependencies on your local machine.
    Using :ref:`reference/system:install` and :ref:`reference/system:verify` you can install all necessary
    dependencies for Unikube and verify their versions.
    """


@click.command()
@click.argument("shell", required=True)
def completion(shell):
    """
    Generate tab completion script for a given shell.
    Supported shells: bash.
    """

    render_completion_script(cli, shell)


# system
system.add_command(system_cmd.install)
system.add_command(system_cmd.verify)
system.add_command(completion)


# organization
@cli.group(cls=DYMGroup, max_suggestions=2, cutoff=0.5)
@click.pass_obj
def orga(ctx):
    """
    Every registered user can belong to one or multiple organisations and can get authorized for the projects of that
    organisation. This command group manages information about your organisations.
    You can see all organizations you belong to with the :ref:`list command<reference/orga:list>`. It presents a
    tabular view of organisations with ``id`` and ``name``. The :ref:`info command<reference/orga:info>` can be used to
    get more detailed information about a particular organisation. This command displays the ``id``, ``title`` and the
    optional description of the organisation. The organisation belongs to the group of selection commands, thus it gives
    three possible options:

        1. you can either manually enter the ``organization_id`` as an optional argument

        2. you can have a context already set with ``organization_id``, then the info for the set organisation will be
           displayed

        3. if none of the above options is specified, you will be prompted with the selection of all possible
           organisations you have access to.

    """


orga.add_command(orga_cmd.list)
orga.add_command(orga_cmd.info)


# project
@cli.group(cls=DYMGroup, max_suggestions=2, cutoff=0.5)
@click.pass_obj
def project(ctx):
    """
    Manage your projects.
    """


project.add_command(project_cmd.list)
project.add_command(project_cmd.info)
project.add_command(project_cmd.up)
project.add_command(project_cmd.down)
project.add_command(project_cmd.delete)
project.add_command(project_cmd.prune)


# deck
@cli.group(cls=DYMGroup, max_suggestions=2, cutoff=0.5)
@click.pass_obj
def deck(ctx):
    """
    Manage all decks you have access to.
    """


deck.add_command(deck_cmd.list)
deck.add_command(deck_cmd.info)
deck.add_command(deck_cmd.install)
deck.add_command(deck_cmd.uninstall)
deck.add_command(deck_cmd.ingress)


# application
@cli.group(cls=DYMGroup, max_suggestions=2, cutoff=0.5)
@click.pass_obj
def app(ctx):
    """
    Manage your applications.
    """


app.add_command(app_cmd.info)
app.add_command(app_cmd.list)
app.add_command(app_cmd.shell)
app.add_command(app_cmd.switch)
app.add_command(app_cmd.logs)
app.add_command(app_cmd.env)
app.add_command(app_cmd.exec)
app.add_command(app_cmd.update)


# authentication
@cli.group(cls=DYMGroup, max_suggestions=2, cutoff=0.5)
def auth():
    """
    The authentication command group unites all subcommands for managing Unikube's authentication process. Besides the
    standard :ref:`reference/auth:login` and :ref:`reference/auth:logout` commands, you can check your current
    authentication status by using :ref:`reference/auth:status` command.
    A valid login state is required for most of the unikube CLI commands.
    """


auth.add_command(auth_cmd.login)
auth.add_command(auth_cmd.logout)
auth.add_command(auth_cmd.status)


# context
@cli.group(cls=DYMGroup, max_suggestions=2, cutoff=0.5)
@click.pass_obj
def context(ctx):
    """
    The ``context`` command group enables you to modify the local context.
    You can :ref:`reference/context:set` and :ref:`reference/context:remove` the organization, project
    and deck context. Use :ref:`reference/context:show` to show the current context.
    """


context.add_command(context_cmd.set)
context.add_command(context_cmd.remove)
context.add_command(context_cmd.show)

# init
cli.add_command(init_cmd.init)

# shortcut
# -> include auth check in functions if required
cli.add_command(auth_cmd.login)
cli.add_command(auth_cmd.logout)
cli.add_command(project_cmd.up)
cli.add_command(deck_cmd.install)
cli.add_command(app_cmd.shell)

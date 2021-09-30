import sys

import click
from click._compat import iteritems
from click.utils import echo

import src.cli.console as console
from src.cli import app as app_cmd
from src.cli import auth as auth_cmd
from src.cli import context as context_cmd
from src.cli import deck as deck_cmd
from src.cli import orga as orga_cmd
from src.cli import project as project_cmd
from src.cli import system as system_cmd
from src.cli import unikube as unikube_cmd
from src.context import ClickContext
from src.helpers import compare_current_and_latest_versions

version = sys.version_info
if version.major == 2:
    console.error("Python 2 is not supported for Unikube. Please upgrade python.", _exit=True)


@click.group()
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
    if not version:
        try:
            import pkg_resources
        except ImportError:
            pass
        else:
            for dist in pkg_resources.working_set:
                scripts = dist.get_entry_map().get("console_scripts") or {}
                for _, entry_point in iteritems(scripts):
                    version = dist.version
                    break
    if version is None:
        raise RuntimeError("Could not determine version")
    echo(f"unikube, version {version}")


cli.add_command(version)
cli.add_command(unikube_cmd.ps)


@cli.group()
@click.pass_obj
def system(ctx):
    """
    The ``system`` command group includes commands to manage system dependencies on your local machine.
    Using :ref:`reference/system:install` and :ref:`reference/system:verify` you can install all necessary
    dependencies for Unikube and verify their versions.
    """


# system
system.add_command(system_cmd.install)
system.add_command(system_cmd.verify)


# organization
@cli.group()
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
@cli.group()
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


# deck
@cli.group()
@click.pass_obj
def deck(ctx):
    """
    Manage all decks you have access to. For further information please refer to
    :ref:`the documentation about decks <provision:What is a Deck?>`.
    """


deck.add_command(deck_cmd.list)
deck.add_command(deck_cmd.info)
deck.add_command(deck_cmd.install)
deck.add_command(deck_cmd.uninstall)
deck.add_command(deck_cmd.ingress)


# application
@cli.group()
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
@cli.group()
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
@cli.group()
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


# shortcut
# -> include auth check in functions if required
cli.add_command(auth_cmd.login)
cli.add_command(auth_cmd.logout)
cli.add_command(project_cmd.up)
cli.add_command(deck_cmd.install)
cli.add_command(app_cmd.shell)


if __name__ == "__main__":
    cli()

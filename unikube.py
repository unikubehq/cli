import sys

import click

import src.cli.console as console
from src.cli import app as app_cmd
from src.cli import auth as auth_cmd
from src.cli import deck as deck_cmd
from src.cli import orga as orga_cmd
from src.cli import project as project_cmd
from src.cli import system as system_cmd
from src.context import ClickContext

version = sys.version_info
if version.major == 2:
    console.error("Python 2 is not supported for Unikube. Please upgrade python.")
    exit(1)


# click -----
@click.group()
@click.version_option()
@click.pass_context
def cli(ctx, **kwargs):
    ctx.obj = ClickContext()


# system
@cli.group()
@click.pass_obj
def system(ctx):
    """
    The ``system`` command group includes commands to manage system dependencies on your local machine.
    Using :ref:`reference/system:install` and :ref:`reference/auth:verify` you can install all necessary
    dependencies for Unikube and verify their versions.
    """


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
    get more detailed information about particular organisation. This command displays the ``id``, ``title`` and the
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
orga.add_command(orga_cmd.use)


# project
@cli.group()
@click.pass_obj
def project(ctx):
    """
    Manage your projects.
    """


project.add_command(project_cmd.list)
project.add_command(project_cmd.info)
project.add_command(project_cmd.use)
project.add_command(project_cmd.up)
project.add_command(project_cmd.down)
project.add_command(project_cmd.delete)


# deck
@cli.group()
@click.pass_obj
def deck(ctx):
    """
    Manage your decks.
    """


deck.add_command(deck_cmd.list)
deck.add_command(deck_cmd.info)
deck.add_command(deck_cmd.use)
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


# shortcut
# -> include auth check in functions if required
cli.add_command(auth_cmd.login)
cli.add_command(auth_cmd.logout)
cli.add_command(project_cmd.up)
cli.add_command(deck_cmd.install)
cli.add_command(app_cmd.shell)


if __name__ == "__main__":
    cli()

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
    console.error("Python 2 is not supported for unikube. Please upgrade python.")
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
    Manage dependencies on your local machine. Install and verify required tools to get your cluster running.
    """


system.add_command(system_cmd.install)
system.add_command(system_cmd.verify)


# organization
@cli.group()
@click.pass_obj
def orga(ctx):
    """
    Manage your organizations.
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
deck.add_command(deck_cmd.logs)
deck.add_command(deck_cmd.request_env)


# application
@cli.group()
@click.pass_obj
def app(ctx):
    """
    Manage your applications.
    """


app.add_command(app_cmd.info)
app.add_command(app_cmd.list)
app.add_command(app_cmd.use)
app.add_command(app_cmd.shell)
app.add_command(app_cmd.switch)
app.add_command(app_cmd.pulldb)
app.add_command(app_cmd.logs)
app.add_command(app_cmd.expose)
app.add_command(app_cmd.env)
app.add_command(app_cmd.request_env)
app.add_command(app_cmd.exec)


# authentication
@cli.group()
def auth():
    """
    Manage Unikube's authentication state.
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

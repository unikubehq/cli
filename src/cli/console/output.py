import click
from tabulate import tabulate

from src import settings


def table(data, headers={}):
    click.echo(
        tabulate(
            data,
            headers=headers,
            tablefmt=settings.CLI_TABLEFMT,
        )
    )

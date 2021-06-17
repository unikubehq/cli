import pytest
from click.testing import CliRunner

from src.cli import app
from unikube import ClickContext
from unittest.mock import patch


def check():
    """Function used to mock check function"""
    pass


def test_shell_cluster_not_found():

    runner = CliRunner()
    obj = ClickContext()
    obj.auth.check = check
    result = runner.invoke(
        app.shell,
        ["test", "test", "test"],
        obj=obj,
    )
    assert "[ERROR] The project cluster could not be found.\n" in result.output


def test_shell_no_cluster_running():

    runner = CliRunner()
    obj = ClickContext()
    obj.auth.check = check
    result = runner.invoke(
        app.shell,
        obj=obj,
    )
    assert "No cluster is running." in result.output




import pytest
from click.testing import CliRunner

from src.cli import app
from unikube import ClickContext
from unittest.mock import patch


def test_shell_cluster_not_found():

    def check():
        pass

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

    def check():
        pass

    runner = CliRunner()
    obj = ClickContext()
    obj.auth.check = check
    result = runner.invoke(
        app.shell,
        obj=obj,
    )
    assert "No cluster is running." in result.output




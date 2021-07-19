from unittest.mock import patch

import pytest
from click.testing import CliRunner

from src.cli import app
from unikube import ClickContext


def check():
    """Function used to mock check function"""
    pass


def test_list():
    runner = CliRunner()
    obj = ClickContext()
    obj.auth.check = check
    result = runner.invoke(
        app.list,
        obj=obj,
    )
    assert result.exit_code == 1


def test_shell_cluster_not_found():
    runner = CliRunner()
    obj = ClickContext()
    obj.auth.check = check
    result = runner.invoke(
        app.shell,
        [
            "test",
            "--organization",
            "13fc0b1b-3bc1-4a69-8e80-835fb1515bc4",
            "--project",
            "13fc0b1b-3bc1-4a69-8e80-835fb1515bc4",
            "--deck",
            "13fc0b1b-3bc1-4a69-8e80-835fb1515bc4",
        ],
        obj=obj,
    )
    assert "[ERROR] The project cluster could not be found or you have another project activated.\n" in result.output

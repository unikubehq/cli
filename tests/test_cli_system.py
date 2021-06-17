import pytest
from click.testing import CliRunner
from src.cli import system
from unikube import ClickContext


def test_system_install():
    runner = CliRunner()
    result = runner.invoke(
        system.install,
        obj=ClickContext(),
    )
    assert "[WARNING] You are not running the installation with an administrative account. You may be prompted for" \
           " your password." in result.output
    assert "[INFO] All dependencies are already satisfied. No action taken." in result.output

    assert result.exit_code == 0


def test_system_verify():
    runner = CliRunner()
    result = runner.invoke(
        system.verify,
        obj=ClickContext(),
    )
    assert "[SUCCESS] Local dependencies verified." in result.output
    assert result.exit_code == 0

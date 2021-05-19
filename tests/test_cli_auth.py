import pytest
from click.testing import CliRunner

from src.cli import auth
from unikube import ClickContext


def test_login():
    runner = CliRunner()
    result = runner.invoke(
        auth.login,
        ["--email", "test@test.de", "--password", "secure"],
        obj=ClickContext(),
    )
    assert result.output == "[ERROR] Login failed. Please check your e-mail or re-enter your password.\n"
    assert result.exit_code == 0


def test_logout():
    runner = CliRunner()
    result = runner.invoke(
        auth.logout,
        obj=ClickContext(),
    )
    assert result.output == "[INFO] Logout completed.\n"
    assert result.exit_code == 0

import pytest
from click.testing import CliRunner

from src.cli import auth
from unikube import ClickContext
from unittest.mock import patch


def test_login():
    runner = CliRunner()
    result = runner.invoke(
        auth.login,
        ["--email", "test@test.de", "--password", "secure"],
        obj=ClickContext(),
    )
    assert result.output == "[ERROR] Login failed. Please check your e-mail or re-enter your password.\n"
    assert result.exit_code == 0


def test_login_wrong_token():

    def login(email, password):
        return {"success": True, "response": {"access_token": "WRONG_TOKEN"}}

    runner = CliRunner()
    obj = ClickContext()
    obj.auth.login = login
    result = runner.invoke(
        auth.login,
        ["--email", "test@test.de", "--password", "secure"],
        obj=obj,
    )
    assert "[ERROR] Login failed. Your token does not match." in result.output
    assert result.exit_code == 0


def test_logout():
    runner = CliRunner()
    result = runner.invoke(
        auth.logout,
        obj=ClickContext(),
    )
    assert result.output == "[INFO] Logout completed.\n"
    assert result.exit_code == 0


def test_status_not_logged():
    runner = CliRunner()
    result = runner.invoke(
        auth.status,
        obj=ClickContext(),
    )
    assert result.output == "[INFO] Authentication could not be verified.\n"
    assert result.exit_code == 0


def test_status_success():

    def verify():
        return {"success": True}

    runner = CliRunner()
    obj = ClickContext()
    obj.auth.verify = verify
    result = runner.invoke(
        auth.status,
        obj=obj,
    )
    assert result.output == "[SUCCESS] Authentication verified.\n"
    assert result.exit_code == 0

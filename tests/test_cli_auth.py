import os
import unittest
from unittest.mock import patch

from click.testing import CliRunner

from src.authentication.authentication import TokenAuthentication
from src.cli import auth
from unikube import ClickContext


class AuthTest(unittest.TestCase):
    def test_login_failed(self):
        runner = CliRunner()
        result = runner.invoke(
            auth.login,
            ["--email", "test@test.de", "--password", "unsecure"],
            obj=ClickContext(),
        )
        assert "[ERROR] Login failed. Please check email and password.\n" in result.output
        assert result.exit_code == 1

    @patch.object(TokenAuthentication, "login")
    def test_login_wrong_token(self, mock_login):
        mock_login.return_value = {"success": True, "response": {"access_token": "WRONG_TOKEN"}}

        runner = CliRunner()
        obj = ClickContext()
        result = runner.invoke(
            auth.login,
            ["--email", "test@test.de", "--password", "secure"],
            obj=obj,
        )
        assert "[ERROR] Login failed." in result.output
        assert result.exit_code == 1

    def test_logout(self):
        runner = CliRunner()
        result = runner.invoke(
            auth.logout,
            obj=ClickContext(),
        )
        assert result.output == "[INFO] Logout completed.\n"
        assert result.exit_code == 0

    def test_status_not_logged(self):
        runner = CliRunner()
        result = runner.invoke(
            auth.status,
            obj=ClickContext(),
        )
        assert result.output == "[INFO] Authentication could not be verified.\n"
        assert result.exit_code == 0

    @patch.object(TokenAuthentication, "verify")
    def test_status_success(self, mock_verify):
        mock_verify.return_value = {"success": True}

        runner = CliRunner()
        obj = ClickContext()
        result = runner.invoke(
            auth.status,
            obj=obj,
        )
        assert result.output == "[SUCCESS] Authentication verified.\n"
        assert result.exit_code == 0

    def test_login_logout_success(self):
        email = os.getenv("TESTRUNNER_EMAIL")
        secret = os.getenv("TESTRUNNER_SECRET")

        self.assertIsNotNone(email)
        self.assertIsNotNone(secret)

        runner = CliRunner()
        result = runner.invoke(
            auth.login,
            ["--email", email, "--password", secret],
            obj=ClickContext(),
        )
        assert "[SUCCESS] Login successful.\n" in result.output
        assert result.exit_code == 0

        result = runner.invoke(
            auth.logout,
            obj=ClickContext(),
        )
        assert result.output == "[INFO] Logout completed.\n"
        assert result.exit_code == 0

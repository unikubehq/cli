import os
import unittest

from click.testing import CliRunner

from src.cli import auth
from unikube import ClickContext


class LoginTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.runner = CliRunner()

        email = os.getenv("TESTRUNNER_EMAIL")
        secret = os.getenv("TESTRUNNER_SECRET")
        self.assertIsNotNone(email)
        self.assertIsNotNone(secret)

        self.runner.invoke(
            auth.login,
            ["--email", email, "--password", secret],
            obj=ClickContext(),
        )

    def tearDown(self) -> None:
        result = self.runner.invoke(
            auth.logout,
            obj=ClickContext(),
        )
        self.assertEqual(result.output, "[INFO] Logout completed.\n")
        self.assertEqual(result.exit_code, 0)

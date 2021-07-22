import os
import unittest

from click.testing import CliRunner

from src.cli import auth, project
from unikube import ClickContext


class ProjectTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.runner = CliRunner()

        email = os.getenv("TESTRUNNER_EMAIL")
        secret = os.getenv("TESTRUNNER_SECRET")
        assert email is not None
        assert secret is not None

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
        assert result.output == "[INFO] Logout completed.\n"
        assert result.exit_code == 0

    def test_project_info(self):
        result = self.runner.invoke(
            project.info,
            ["buzzword-counter"],
            obj=ClickContext(),
        )

        self.assertIn("Key", result.output)
        self.assertIn("Value", result.output)
        self.assertIn("buzzword-counter", result.output)
        assert result.exit_code == 0

    def test_project_list(self):

        result = self.runner.invoke(
            project.list,
            obj=ClickContext(),
        )

        self.assertIn("Id", result.output)
        self.assertIn("name", result.output)
        self.assertIn("buzzword-counter", result.output)
        assert result.exit_code == 0

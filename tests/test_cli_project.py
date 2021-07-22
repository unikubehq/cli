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

    def test_project_info(self):
        result = self.runner.invoke(
            project.info,
            ["buzzword-counter"],
            obj=ClickContext(),
        )

        self.assertIn("Key", result.output)
        self.assertIn("Value", result.output)
        self.assertIn("buzzword-counter", result.output)
        self.assertEqual(result.exit_code, 0)

    def test_project_list(self):

        result = self.runner.invoke(
            project.list,
            obj=ClickContext(),
        )

        self.assertIn("Id", result.output)
        self.assertIn("name", result.output)
        self.assertIn("buzzword-counter", result.output)
        self.assertEqual(result.exit_code, 0)

    def test_project_use_failing(self):
        result = self.runner.invoke(
            project.use,
            obj=ClickContext(),
        )

        self.assertIn("Please select a project: buzzword-counter", result.output)
        self.assertEqual(result.exit_code, 1)

    def test_project_use(self):
        result = self.runner.invoke(
            project.use,
            ["ed5390e7-16f6-4f6c-9b7b-5f3bd2db1718"],
            obj=ClickContext(),
        )

        self.assertIn("[SUCCESS] Project context: organization_id=", result.output)
        self.assertEqual(result.exit_code, 0)

    def test_project_use_remove(self):
        result = self.runner.invoke(
            project.use,
            ["-r"],
            obj=ClickContext(),
        )

        self.assertIn("[SUCCESS] Project context removed.\n", result.output)
        self.assertEqual(result.exit_code, 0)

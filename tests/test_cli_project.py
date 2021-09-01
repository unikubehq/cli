from src.cli import orga, project
from tests.login_testcase import LoginTestCase
from unikube import ClickContext


class ProjectTestCase(LoginTestCase):
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

    def test_info_not_existing_project(self):
        result = self.runner.invoke(
            project.info,
            ["not-existing-project"],
            obj=ClickContext(),
        )

        self.assertIn("[ERROR] Project name/slug does not exist.\n", result.output)

    def test_project_list(self):
        result = self.runner.invoke(
            project.list,
            obj=ClickContext(),
        )

        self.assertIn("id", result.output)
        self.assertIn("name", result.output)
        self.assertIn("buzzword-counter", result.output)
        self.assertEqual(result.exit_code, 0)

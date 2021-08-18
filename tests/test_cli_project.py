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

        self.assertIn("[ERROR] Project does not exist.", result.output)

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
            ["b464a6a7-7367-41d3-92a3-d3d98ed10cb5"],
            obj=ClickContext(),
        )
        remove_project_ctx = self.runner.invoke(
            project.use,
            ["-r"],
            obj=ClickContext(),
        )
        remove_orga_ctx = self.runner.invoke(
            orga.use,
            ["-r"],
            obj=ClickContext(),
        )

        self.assertIn("[SUCCESS] Project context: organization_id=", result.output)
        self.assertIn("[SUCCESS] Project context removed.\n", remove_project_ctx.output)
        self.assertIn("[SUCCESS] Organization context removed.\n", remove_orga_ctx.output)
        self.assertEqual(result.exit_code, 0)

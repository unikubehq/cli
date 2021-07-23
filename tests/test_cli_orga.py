from click.testing import CliRunner

from src.cli import orga
from tests.login_testcase import LoginTestCase
from unikube import ClickContext


def test_orga_list():
    runner = CliRunner()
    result = runner.invoke(
        orga.list,
        obj=ClickContext(),
    )
    assert result.exit_code == 1


class OrgaTestCase(LoginTestCase):
    def test_orga_info(self):
        result = self.runner.invoke(
            orga.info,
            ["ACME"],
            obj=ClickContext(),
        )

        self.assertIn("Key", result.output)
        self.assertIn("Value", result.output)
        self.assertIn("title", result.output)
        self.assertIn("ACME", result.output)
        self.assertEqual(result.exit_code, 0)

    def test_orga_list(self):

        result = self.runner.invoke(
            orga.list,
            obj=ClickContext(),
        )

        self.assertIn("id", result.output)
        self.assertIn("name", result.output)
        self.assertIn("acme", result.output)
        self.assertEqual(result.exit_code, 0)

    def test_orga_use_failing(self):
        result = self.runner.invoke(
            orga.use,
            obj=ClickContext(),
        )

        self.assertIn("[?] Please select an organization: ACME", result.output)
        self.assertEqual(result.exit_code, 1)

    def test_orga_use(self):
        result = self.runner.invoke(
            orga.use,
            ["ceba2255-3113-4a2c-af7a-7e0c9e73cd0c"],
            obj=ClickContext(),
        )

        self.assertIn("[SUCCESS] Organization context: organization_id=", result.output)
        self.assertEqual(result.exit_code, 0)

    def test_orga_use_remove(self):
        result = self.runner.invoke(
            orga.use,
            ["-r"],
            obj=ClickContext(),
        )

        self.assertIn("[SUCCESS] Organization context removed.\n", result.output)
        self.assertEqual(result.exit_code, 0)

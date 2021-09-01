from src.cli import orga
from tests.login_testcase import LoginTestCase
from unikube import ClickContext


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

    def test_info_not_existing_orga(self):
        result = self.runner.invoke(
            orga.info,
            "not_existing_orga",
            obj=ClickContext(),
        )
        self.assertIn("[ERROR] Organization name/slug does not exist.\n", result.output)

    def test_orga_list(self):

        result = self.runner.invoke(
            orga.list,
            obj=ClickContext(),
        )

        self.assertIn("id", result.output)
        self.assertIn("name", result.output)
        self.assertIn("acme", result.output)
        self.assertEqual(result.exit_code, 0)

from click.testing import CliRunner

from src.cli import system
from tests.login_testcase import LoginTestCase
from unikube import ClickContext


class SystemTestCase(LoginTestCase):
    def test_system_install(self):
        result = self.runner.invoke(
            system.install,
            obj=ClickContext(),
        )
        self.assertIn(
            "[WARNING] You are not running the installation with an administrative account. You may be prompted for"
            " your password.",
            result.output,
        )
        self.assertIn("[INFO] All dependencies are already satisfied. No action taken.", result.output)
        self.assertEqual(result.exit_code, 0)

    def test_system_verify(self):
        result = self.runner.invoke(
            system.verify,
            obj=ClickContext(),
        )

        self.assertIn("[SUCCESS] Local dependencies verified.", result.output)
        self.assertEqual(result.exit_code, 0)

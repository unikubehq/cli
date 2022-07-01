from unittest.mock import patch

from tests.login_testcase import LoginTestCase
from unikube.authentication.authentication import TokenAuthentication
from unikube.cli import app
from unikube.context import ClickContext


class AppTestCase(LoginTestCase):
    @patch.object(TokenAuthentication, "check")
    def test_list(self, *args, **kwargs):
        obj = ClickContext()
        result = self.runner.invoke(
            app.list,
            obj=obj,
        )
        assert result.exit_code == 1

    @patch.object(TokenAuthentication, "check")
    def test_shell_invalid_arguments(self, *args, **kwargs):
        obj = ClickContext()
        result = self.runner.invoke(
            app.shell,
            [
                "test",
                "--organization",
                "13fc0b1b-3bc1-4a69-8e80-835fb1515bc4",
                "--project",
                "13fc0b1b-3bc1-4a69-8e80-835fb1515bc4",
                "--deck",
                "13fc0b1b-3bc1-4a69-8e80-835fb1515bc4",
            ],
            obj=obj,
        )
        assert "[ERROR] Something went wrong!\n" in result.output

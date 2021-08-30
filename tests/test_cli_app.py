from src.cli import app
from tests.login_testcase import LoginTestCase
from unikube import ClickContext


def check():
    """Function used to mock check function"""
    pass


class AppTestCase(LoginTestCase):
    def test_list(self):
        obj = ClickContext()
        obj.auth.check = check
        result = self.runner.invoke(
            app.list,
            obj=obj,
        )
        assert result.exit_code == 1

    def test_shell_invalid_arguments(self):
        obj = ClickContext()
        obj.auth.check = check
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

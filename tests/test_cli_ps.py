from src.cli.unikube import ps
from tests.login_testcase import LoginTestCase
from unikube import ClickContext


class PsTest(LoginTestCase):
    def test_no_cluster(self):
        result = self.runner.invoke(
            ps,
            obj=ClickContext(),
        )
        self.assertEqual(result.exit_code, 0)

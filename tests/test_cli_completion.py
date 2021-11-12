import unittest

from click.testing import CliRunner

from unikube import ClickContext, completion


class CompletionTest(unittest.TestCase):
    def setUp(self) -> None:
        self.runner = CliRunner()

    def test_no_cluster(self):
        result = self.runner.invoke(
            completion,
            ["bash"],
            obj=ClickContext(),
        )
        self.assertEqual(result.exit_code, 0)

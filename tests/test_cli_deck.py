import os
import unittest

from click.testing import CliRunner

from src.cli import auth, deck
from unikube import ClickContext


def check():
    """Function used to mock check function"""
    pass


def test_list():
    runner = CliRunner()
    obj = ClickContext()
    obj.auth.check = check
    result = runner.invoke(
        deck.list,
        [
            "--organization",
            "13fc0b1b-3bc1-4a69-8e80-835fb1515bc4",
            "--project",
            "13fc0b1b-3bc1-4a69-8e80-835fb1515bc4",
        ],
        obj=obj,
    )
    assert result.exit_code == 1


def test_info():
    runner = CliRunner()
    obj = ClickContext()
    obj.auth.check = check
    result = runner.invoke(
        deck.info,
        [
            "13fc0b1b-3bc1-4a69-8e80-835fb1515bc4",
        ],
        obj=obj,
    )
    assert result.exit_code == 1


def test_ingress():
    runner = CliRunner()
    obj = ClickContext()
    obj.auth.check = check
    result = runner.invoke(
        deck.ingress,
        [
            "13fc0b1b-3bc1-4a69-8e80-835fb1515bc4",
        ],
        obj=obj,
    )
    assert result.exit_code == 1


class DeckTestCase(unittest.TestCase):
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

    def test_deck_info(self):
        result = self.runner.invoke(
            deck.info,
            ["buzzword-counter"],
            obj=ClickContext(),
        )

        self.assertIn("Key", result.output)
        self.assertIn("Value", result.output)
        self.assertIn("buzzword-counter", result.output)
        self.assertEqual(result.exit_code, 0)

    def test_deck_list(self):

        result = self.runner.invoke(
            deck.list,
            obj=ClickContext(),
        )

        self.assertIn("project", result.output)
        self.assertIn("id", result.output)
        self.assertIn("title", result.output)
        self.assertIn("buzzword-counter", result.output)
        self.assertEqual(result.exit_code, 0)

    def test_deck_use_failing(self):
        result = self.runner.invoke(
            deck.use,
            obj=ClickContext(),
        )

        self.assertIn("\n[?] Please select a deck: buzzword-counter\n > buzzword-counter\n\n", result.output)
        self.assertEqual(result.exit_code, 1)

    def test_deck_use(self):
        result = self.runner.invoke(
            deck.use,
            ["4634368f-1751-40ae-9cd7-738fcb656a0d"],
            obj=ClickContext(),
        )

        self.assertIn("[SUCCESS] Deck context: organization_id=", result.output)
        self.assertEqual(result.exit_code, 0)

    def test_deck_use_remove(self):
        result = self.runner.invoke(
            deck.use,
            ["-r"],
            obj=ClickContext(),
        )

        self.assertIn("[SUCCESS] Deck context removed.\n", result.output)
        self.assertEqual(result.exit_code, 0)

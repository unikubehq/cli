from src.cli import deck
from tests.login_testcase import LoginTestCase
from unikube import ClickContext


class DeckTestCase(LoginTestCase):
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

    def test_info_not_existing_deck(self):

        result = self.runner.invoke(
            deck.info,
            ["not_existing_deck"],
            obj=ClickContext(),
        )
        self.assertIn("[ERROR] Deck name/slug does not exist.\n", result.output)

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

    def test_deck_ingress(self):
        result = self.runner.invoke(
            deck.ingress,
            ["4634368f-1751-40ae-9cd7-738fcb656a0d"],
            obj=ClickContext(),
        )

        self.assertIn(
            "[ERROR] The project cluster does not exist. Please be sure to run 'unikube project up' first.\n",
            result.output,
        )
        self.assertEqual(result.exit_code, 1)

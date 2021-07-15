from click.testing import CliRunner

from src.cli import deck
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

from click.testing import CliRunner

from src.cli import orga
from unikube import ClickContext


def test_login():
    runner = CliRunner()
    result = runner.invoke(
        orga.list,
        obj=ClickContext(),
    )
    assert "[DEBUG] Refresh token expired or account does not exist." in result.output
    assert "[INFO] You need to login (again). Please run 'unikube login' and try again." in result.output

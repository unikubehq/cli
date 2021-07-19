from click.testing import CliRunner

from src.cli import orga
from unikube import ClickContext


def test_orga_list():
    runner = CliRunner()
    result = runner.invoke(
        orga.list,
        obj=ClickContext(),
    )
    assert result.exit_code == 1

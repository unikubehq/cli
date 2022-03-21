from glob import glob
from os.path import getctime
from urllib.parse import quote

import click

from unikube.cli import console
from unikube.settings import CLI_KUBECONFIG_DIRECTORY


@click.command()
def submit():
    """Opens the latest error log as an Github issue in the default browser."""
    file_list = glob(f"{CLI_KUBECONFIG_DIRECTORY}*.log")
    latest_report = max(file_list, key=getctime)

    with open(latest_report, "r") as f:
        url = "https://github.com/unikubehq/cli/issues/new?title={title}&body={report}".format(
            title="", report=quote(f.read())
        )

        click.launch(url)
    console.info("Thanks you very much for helping us improve unikube!")

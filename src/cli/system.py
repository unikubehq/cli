import os
import sys

import click
from tabulate import tabulate

import src.cli.console as console
from src import settings
from src.local.dependency import install_dependency, probe_dependencies


@click.command()
@click.option("--reinstall", help="Reinstall the given dependencies")
def install(reinstall):
    """
    Install dependencies on your local machine.
    """

    def _do_install():
        incomplete = []
        successful = []
        unsuccessful = []
        for dependency in dependencies:
            rcode = install_dependency(dependency["name"])
            # since this run can contain multiple installations, capture all return codes
            if rcode is None:
                incomplete.append(dependency["name"])
            elif rcode == 0:
                successful.append(dependency["name"])
            elif rcode != 0:
                unsuccessful.append(dependency["name"])
        if unsuccessful:
            console.error("Some of the requested installations terminated unsuccessful")
        elif successful and not unsuccessful and not incomplete:
            # this only become 0 if installation actually run and was successful
            console.success("All requested dependencies installed successfully")
        elif incomplete:
            console.warning("Not all dependencies could be installed")

    # check account permission
    if os.geteuid() != 0:
        console.warning(
            "You are not running the installation with an administrative account. "
            "You may be prompted for your password."
        )

    # install
    if reinstall:
        dependencies = [{"name": i} for i in reinstall.split(",")]
    else:
        report_data = probe_dependencies(silent=True)
        dependencies = list(filter(lambda x: not x["success"], report_data))
        if len(dependencies) == 1:
            console.info(f"The following dependency is going to be installed: {dependencies[0]['name']}")
        elif len(dependencies) > 1:
            console.info(
                f"The following dependencies are going to be " f"installed: {','.join(k['name'] for k in dependencies)}"
            )
        else:
            console.info("All dependencies are already satisfied. No action taken.")
            sys.exit(0)

    _do_install()


@click.command()
@click.option("--verbose", "-v", is_flag=True, default=False, help="")
def verify(verbose):
    """
    Verifies the installation of dependencies on your local machine.
    """

    report_data = probe_dependencies(silent=verbose)
    unsuccessful = list(filter(lambda x: not x["success"], report_data))

    # show detailed table
    if verbose:
        successful = list(filter(lambda x: x["success"], report_data))

        console.table(
            successful + unsuccessful,
            headers={
                "name": "Name",
                "success": "Ok",
                "required_version": "Required Version",
                "installed_version": "Installed Version",
                "msg": "Message",
            },
        )

    if unsuccessful:
        console.error(
            f"There {'is' if len(unsuccessful) == 1 else 'are'} {len(unsuccessful)} (of {len(report_data)}) "
            f"unsuccessfully probed {'dependency' if len(unsuccessful) == 1 else 'dependencies'} on your "
            f"local machine. Please run 'unikube system install' in order to fix "
            f"these issues."
        )
        return False

    console.success("Local dependencies verified.")

    return True

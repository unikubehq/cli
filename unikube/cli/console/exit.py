import sys
from datetime import datetime

from click import get_current_context

from unikube import settings
from unikube.cli.console.logger import error, info
from unikube.helpers import get_current_version


def exit_login_required():
    info("You need to login (again). Please run 'unikube login' and try again.")
    exit(1)


def _get_unikube_path(path: str):
    splitted_path = path.split("/")
    index = splitted_path.index("unikube")
    new_splitted_path = splitted_path[index:]
    return "/".join(new_splitted_path)


def exit_generic_error():
    error("\033[91m✘ Oh no! Something unexpected happened!\033[0m")
    info("We're really sorry! It seems we haven't covered this error in unikube yet.")
    date_string = datetime.today().strftime("%Y_%m_%d-%H_%M_%S")
    file_path = f"{settings.CLI_KUBECONFIG_DIRECTORY}error_{date_string}.log"
    exec_info = sys.exc_info()
    click_context = get_current_context()
    with open(file_path, "w") as f:
        f.write("Traceback information:\n")
        f.write("\n```\n")
        f.write(f"Exception: {exec_info[0].__name__}\n")
        f.write(f"Value: {exec_info[1]}\n")
        f.write(
            f"File: {str(_get_unikube_path(exec_info[2].tb_frame.f_code.co_filename))} Line: "
            f"{str(exec_info[2].tb_lineno)}\n"
        )
        f.write("```\n\n")
        f.write("--------------------------\n\n")
        version = get_current_version()
        if version:
            f.write(f"unikube version: {version}\n")
        else:
            f.write(f"unikube version: unknown\n")
        if click_context:
            f.write(f"command: `")
            try:
                if click_context.parent.command.name:
                    f.write(f"{click_context.parent.command.name} ")
            except AttributeError:
                pass
            f.write(f"{click_context.command.name} ")
            if click_context.invoked_subcommand:
                f.write(click_context.invoked_subcommand)
            f.write("`\n")
    info(f"In case you're curious we wrote an error log to: {file_path}")
    info(f"Please help us improving unikube by submitting the error by running:")
    info(f"unikube issue submit")
    exit(1)

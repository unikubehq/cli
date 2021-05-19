from src.cli.console.logger import error, info


def exit_login_required():
    info("Login required.")
    exit(1)


def exit_generic_error():
    error("Something went wrong!")
    exit(1)

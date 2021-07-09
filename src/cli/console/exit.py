from src.cli.console.logger import error, info


def exit_login_required():
    info("You need to login (again). Please run 'unikube login' and try again.")
    exit(1)


def exit_generic_error():
    error("Something went wrong!")
    exit(1)

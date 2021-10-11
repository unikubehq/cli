from enum import Enum

import click

from src import settings


# log level
class LogLevel(str, Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"


log_level_mapping = {
    LogLevel.DEBUG: [LogLevel.DEBUG],
    LogLevel.INFO: [LogLevel.DEBUG, LogLevel.INFO],
    LogLevel.WARNING: [LogLevel.DEBUG, LogLevel.INFO, LogLevel.WARNING],
    LogLevel.ERROR: None,  # None -> print always
    LogLevel.SUCCESS: None,
}

# color
color_mapping = {
    LogLevel.DEBUG: "cyan",
    LogLevel.INFO: "",
    LogLevel.WARNING: "yellow",
    LogLevel.ERROR: "red",
    LogLevel.SUCCESS: "green",
}


# helper
def _click_secho(
    msg: str, silent: bool, log_level: str = None, _exit: bool = False, _exit_code: int = 1, color=None, **kwargs
):
    # get log level settings and console mapping
    setting_log_level = LogLevel(settings.CLI_LOG_LEVEL.lower())
    console_log_level = log_level_mapping.get(log_level, None)

    # check log level
    if console_log_level is None:
        pass  # log level independent

    else:
        if setting_log_level not in console_log_level:
            return None

    # silence message?
    if silent:
        return None

    # color
    if color:
        fg = color
    else:
        fg = color_mapping.get(log_level, "")

    # console echo
    if log_level:
        click.secho(f"[{log_level.value.upper()}] {msg}", fg=fg, **kwargs)
    else:
        click.secho(msg, fg=fg, **kwargs)

    # exit
    if _exit:
        exit(_exit_code)


# console output
def debug(msg: str, silent: bool = False, **kwargs):
    _click_secho(msg, silent, log_level=LogLevel.DEBUG, **kwargs)


def echo(msg: str, silent: bool = False, _exit: bool = False, _exit_code: int = 1, **kwargs):
    _click_secho(msg=msg, silent=silent, log_level=None, _exit=_exit, _exit_code=_exit_code, **kwargs)


def info(msg: str, silent: bool = False, _exit: bool = False, _exit_code: int = 1, **kwargs):
    _click_secho(msg=msg, silent=silent, log_level=LogLevel.INFO, _exit=_exit, _exit_code=_exit_code, **kwargs)


def warning(msg: str, silent: bool = False, _exit: bool = False, _exit_code: int = 1, **kwargs):
    _click_secho(msg=msg, silent=silent, log_level=LogLevel.WARNING, _exit=_exit, _exit_code=_exit_code, **kwargs)


def error(msg: str, _exit: bool = False, _exit_code: int = 1, **kwargs):
    _click_secho(msg=msg, silent=False, log_level=LogLevel.ERROR, _exit=_exit, _exit_code=_exit_code, **kwargs)


def success(msg: str, silent: bool = False, **kwargs):
    _click_secho(msg=msg, silent=silent, log_level=LogLevel.SUCCESS, **kwargs)


def link(msg: str, silent: bool = False, _exit: bool = False, _exit_code: int = 1, **kwargs):
    _click_secho(msg=msg, silent=silent, log_level=None, _exit=_exit, _exit_code=_exit_code, color="cyan", **kwargs)

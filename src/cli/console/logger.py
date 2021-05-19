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
def _click_secho(msg, silent, log_level=None, **kwargs):
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
    fg = color_mapping.get(log_level, "")

    # console echo
    click.secho(f"[{log_level.value.upper()}] {msg}", fg=fg, **kwargs)


# console output
def debug(msg, silent=False, **kwargs):
    _click_secho(msg, silent, log_level=LogLevel.DEBUG, **kwargs)


def info(msg, silent=False, **kwargs):
    _click_secho(msg, silent, log_level=LogLevel.INFO, **kwargs)


def warning(msg, silent=False, **kwargs):
    _click_secho(msg, silent, log_level=LogLevel.WARNING, **kwargs)


def error(msg, _exit: bool = False, **kwargs):
    _click_secho(msg, silent=False, log_level=LogLevel.ERROR, **kwargs)

    # exit
    if _exit:
        exit(1)


def success(msg, silent=False, **kwargs):
    _click_secho(msg, silent, log_level=LogLevel.SUCCESS, **kwargs)

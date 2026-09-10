"""Coloured logging setup for TrajGenPy.

This module configures a :mod:`logging` logger named ``"trajgenpy"`` with
ANSI colour formatting via `colorama <https://pypi.org/project/colorama/>`_.
Each log level is rendered in a distinct colour:

- **TRACE** – magenta
- **DEBUG** – blue
- **INFO** – green
- **WARNING** – yellow
- **ERROR** – red

The logger is initialised automatically when the module is first imported.
All TrajGenPy modules obtain the logger via :func:`get_logger`.
"""

import inspect
import logging
from pathlib import Path

import colorama

LOGGER_NAME = "trajgenpy"


def init_logger():
    """Initialise and return the ``"trajgenpy"`` logger.

    Creates a :class:`logging.StreamHandler` with a
    :class:`~logging.Formatter` that prepends ANSI colour codes to the log
    level name and appends the originating file name and line number.  The
    logger level is set to ``DEBUG`` so that all messages are forwarded to
    handlers; adjust individual handlers if a higher threshold is desired.

    Calling this function more than once is safe — the handler is always
    attached, but :func:`get_logger` should be preferred for normal usage
    as it returns the existing logger without re-initialising it.

    Returns:
        logging.Logger: The configured ``"trajgenpy"`` logger instance.
    """
    # Initialize colorama to support ANSI color codes on Windows
    colorama.init()

    # Define custom log levels and their corresponding colors
    LOG_COLORS = {
        "TRACE": colorama.Fore.MAGENTA,
        "DEBUG": colorama.Fore.BLUE,
        "INFO": colorama.Fore.GREEN,
        "WARNING": colorama.Fore.YELLOW,
        "ERROR": colorama.Fore.RED,
    }

    class ColoredFormatter(logging.Formatter):
        def format(self, record):
            log_level = record.levelname
            color = LOG_COLORS.get(log_level, "")
            reset = colorama.Style.RESET_ALL
            frame_info = inspect.stack()[-1]
            filename = Path(frame_info[1])
            record.filename = filename.name
            record.levelname = f"{color}{log_level}{reset}"
            return super().format(record)

    logger = logging.getLogger(LOGGER_NAME)
    log_format = "%(asctime)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)"

    formatter = ColoredFormatter(log_format)
    logger.setLevel(logging.DEBUG)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    logger.addHandler(stream_handler)
    return logger


def get_logger():
    """Return the ``"trajgenpy"`` logger.

    If the logger has not been initialised yet (no handlers attached),
    :func:`init_logger` is called automatically.  This function is the
    preferred way to obtain the logger from within TrajGenPy modules.

    Returns:
        logging.Logger: The ``"trajgenpy"`` logger instance.
    """
    return logging.getLogger(LOGGER_NAME)


if get_logger().handlers == []:
    init_logger()

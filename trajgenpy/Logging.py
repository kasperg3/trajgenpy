import logging
from re import DEBUG

from colorama import Fore, Style, init
import os

# Initialize colorama to support ANSI color codes on Windows
init()

# Define custom log levels and their corresponding colors
LOG_COLORS = {
    "TRACE": Fore.MAGENTA,
    "DEBUG": Fore.BLUE,
    "INFO": Fore.GREEN,
    "WARNING": Fore.YELLOW,
    "ERROR": Fore.RED,
}


class ColoredFormatter(logging.Formatter):
    def format(self, record):
        log_level = record.levelname
        color = LOG_COLORS.get(log_level, "")
        reset = Style.RESET_ALL
        record.levelname = f"{color}{log_level}{reset}"
        # record.msg = f"{color}{record.msg}{reset}"
        return super().format(record)


logger = logging.getLogger(os.path.basename(__file__))
log_format = "%(asctime)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)"

formatter = ColoredFormatter(log_format)
logger.setLevel(logging.DEBUG)

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)

logger.addHandler(stream_handler)


def debug(*args, **kwargs):
    message = " ".join(map(str, args))
    logger.debug(message, **kwargs)


def info(*args, **kwargs):
    message = " ".join(map(str, args))
    logger.info(message, **kwargs)


def warning(*args, **kwargs):
    message = " ".join(map(str, args))
    logger.warning(message, **kwargs)


def error(*args, **kwargs):
    message = " ".join(map(str, args))
    logger.error(message, **kwargs)


if __name__ == "__main__":
    debug("This is a debug message")
    info("This is an info message")
    warning("This is a warning message")
    error("This is an error message")

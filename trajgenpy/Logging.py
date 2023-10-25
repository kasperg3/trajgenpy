import inspect
import logging
from pathlib import Path

import colorama

LOGGER_NAME = "trajgenpy"


def init_logger():
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
    return logging.getLogger(LOGGER_NAME)


if get_logger().handlers == []:
    init_logger()


# def debug(*args, **kwargs):
#     message = " ".join(map(str, args))
#     logging.getLogger(LOGGER_NAME).debug(message, **kwargs)


# def info(*args, **kwargs):
#     message = " ".join(map(str, args))
#     logging.getLogger(LOGGER_NAME).info(message, **kwargs)


# def warning(*args, **kwargs):
#     message = " ".join(map(str, args))
#     logging.getLogger(LOGGER_NAME).warning(message, **kwargs)


# def error(*args, **kwargs):
#     message = " ".join(map(str, args))
#     logging.getLogger(LOGGER_NAME).error(message, **kwargs)


# if __name__ == "__main__":
#     debug("This is a debug message")
#     info("This is an info message")
#     warning("This is a warning message")
#     error("This is an error message")

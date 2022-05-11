# Reference:
#   https://stackoverflow.com/questions/65461959/calling-a-static-method-with-self-vs-class-name

import logging
import logging.handlers


formatter = logging.Formatter("%(asctime)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

def setup_logger(name: str, log_file: str, level=logging.INFO) -> logging.Logger:
    """Returns a new logger.

    Arguments:
        name: Name of the logger.
        log_file: Where the logger logs to.
        level: Logging messages which are less severe than level will be ignored.
    """
    handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=6_000, backupCount=1)
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger

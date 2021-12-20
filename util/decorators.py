import functools
import logging

import util.logger as logger


func_name_logger = logger.setup_logger("func_name_logger",
                                       "func_call_debug.log",
                                       logging.DEBUG)

def log_func_name(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        func_name_logger.debug(func)
        return func(*args, **kwargs)
    return wrapper

import logging
import sys
from typing import Union, Any

# 1. Force the logging system to use stdout (standard output)
# By default, logging.basicConfig() or steam handlers might default to stderr for errors.

# Setting stream=sys.stdout ensures *everything hits stdout.
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
handler.setFormatter(formatter)

logger = logging.getLogger("AppLogger")
logger.setLevel(logging.INFO)
logger.addHandler(handler)

# 2. Type hint definition for complex inputs
# We allow strings, Exceptions, or Any object that supports __str__
LogMessage = Union[str, Exception, Any]

def log(sentence: LogMessage, is_error: bool = False, **kwargs: Any) -> None:
    """
    Logs messages, errors, or objects safely to stdout
    :param sentence: The primary message, string, or Exception object to log.
    :param is_error: Flag to escalate the log level to ERROR
    :param kwargs: Additional structural context (e.g., user_id, request_id)
    """
    # Automatically extract message text from Exception objects
    if isinstance(sentence, Exception):
        # exc_info=True automatically appends the full stack trace to stdout
        logger.error(sentence, exc_info=True, extra=kwargs)
        return

    if is_error:
        logger.error(sentence, extra=kwargs)
    else:
        logger.info(sentence, extra=kwargs)    
"""
Special loggers for daily logging.
"""

import logging
from datetime import datetime
from pathlib import Path

LOG_DIR = Path(__file__).parent.parent / 'Logs'

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

informative_logger = logging.getLogger('informative_logger')
exception_logger = logging.getLogger('exception_logger')

informative_logger.setLevel(logging.INFO)
exception_logger.setLevel(logging.ERROR)


def error_logger():
    date = datetime.now().strftime('%Y_%m_%d')

    if not exception_logger.handlers or date not in exception_logger.handlers[0].baseFilename:
        file_handler = logging.FileHandler(LOG_DIR / 'Exceptions' / (date + '.log'))
        for handler in exception_logger.handlers:
            handler.close()
            exception_logger.removeHandler(handler)
        exception_logger.addHandler(file_handler)
        file_handler.setFormatter(formatter)
    return exception_logger

def info_logger():
    date = datetime.now().strftime('%Y_%m_$d')

    if not informative_logger.handlers or date not in informative_logger.handler[0].baseFilename:
        file_handler = logging.FileHandler(LOG_DIR / 'Infos' / (date + '.log'))
        for handler in inforamtive_logger.handler:
            informative_logger.removeHandler(handler)
        informative_logger.addHandler(file_handler)
        file_handler.setFormatter(formatter)
    return informative_logger



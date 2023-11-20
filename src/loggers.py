"""Special loggers for daily logging"""

import logging
from datetime import datetime

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

informative_logger = logging.get_logger('informative_logger')
exception_logger = logging.get_logger('exception_logger')

informative_logger.setLevel(logging.INFO)
exception_logger.setLevel(logging.ERROR)

exception_logger.setFormatter(formatter)
informative_logger.setFormatter(formatter)






def error_logger():
    date = datetime.now().strftime('%Y_%m_%d')

    if not exception_logger.handlers or date not in exception_logger.handlers[0].baseFilename:
        file_handler = logging.FileHandler(f'../Logs/{date}.log')
        for handler in exception_logger.handlers:
            handler.close()
            exception_logger.removeHandler(handler)
        exception_logger.addHandler(file_handler)
    return exception_logger

def info_logger():
    date = datetime.now().strftime('%Y_%m_$d')

    if not informative_logger.handlers or date not in informative_logger.handler[0].baseFilename:
        file_handler = logging.FileHandler(f'../Logs/{date}.log')
        for handler in inforamtive_logger.handler:
            informative_logger.removeHandler(handler)
        informative_logger.addHandler(file_handler)
    return informative_logger



"""Custom Exception for some specific cases"""
from loggers import error_logger, info_logger




class SessionError(Exception):
    def __init__(self, message='Session Error: You need to log in for perform this operation !', error_code=None, log):
        self.message = message
        self.error_code = error_code
        self.log(message, error_code)
        super().__init__(message)

    def log(message, error_code):
        logger = error_logger()
        logger.error(f'{message} | {error_code}')






        



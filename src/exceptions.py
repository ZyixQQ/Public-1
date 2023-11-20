"""Custom Exception for some specific cases"""
from loggers import error_logger, info_logger




class SessionError(Exception):
    def __init__(self, message='Session Error: You need to log in for perform this operation !', error_code=None):
        self.message = message
        self.error_code = error_code
        self.log(message, error_code)
        super().__init__(message)

    def log(self, message, error_code):
        logger = error_logger()
        logger.error(f'{message} | {error_code}')





class UserNotExistError(Exception):
    def __init__(self, message='UserNotExistError: Given username, password or id is wrong, specified user couldnt found !', error_code=None):
        self.message = message
        self.error_code = error_code
        self.log(message, error_code)

    def log(self, message, error_code):
        logger = exception_logger()
        logger.error(f'{message} | {error_code}')







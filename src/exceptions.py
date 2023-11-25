"""Custom Exception for some specific cases"""
from loggers import error_logger, info_logger




class SessionError(Exception):
    '''
    This error class is used when there is an error related to sessions (login, logout, etc.).
    '''
    def __init__(self, message='You need to log in for perform this operation !', error_code=None):
        self.message = message
        self.error_code = error_code
        self.log(message, error_code)
        super().__init__(message)

    def log(self, message, error_code):
        logger = error_logger()
        logger.error(f'{message} | Code: {error_code}')





class UserNotExistError(Exception):
    '''
    This error class is used when there are no users to process.
    '''
    def __init__(self, message='Given username, password or id is wrong, specified user couldnt found !', error_code=None):
        self.message = message
        self.error_code = error_code
        self.log(message, error_code)

    def log(self, message, error_code):
        logger = exception_logger()
        logger.error(f'{message} | Code: {error_code}')


class IncorrectOptionError(Exception):
    '''
    This error class is used when the user selects an option that does not exist or incorrect.
    '''
    def __init__(self, message='You have chosen an option that is not valid.', error_code=None):
        self.message = message
        self.error_code = error_code
        self.log(message, error_code)
    
    def log(self, message, error_code):
        logger = exception_logger()
        logger.error(f'{message} | Code: {error_code}')



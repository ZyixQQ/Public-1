"""Decorator source for Bank project"""
from functools import wraps
from exceptions import SessionError

def admin_required(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if self.user and getattr(self.user, 'is_admin', False):
            return func(self, *args, **kwargs)
        else:
            raise PermissionError(f'Permission Denied: You dont have required permissions to perform this operation (func.__name__)!')
    return wrapper


def login_required(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if getattr(self, 'user', None):
            return func(self, *args, **kwargs)
        else:
            raise SessionError(f'SessionError: You should log in to perform this operation (func.__name__). Please log in !')
    return wrapper

def logout_required(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if getattr(self, 'user', None) is None:
            return func(self, *args, **kwargs)
        else:
            raise SessionError(f'SessionError: You should log out for perform this operation (func.__name__). Please log out !')
    return wrapper

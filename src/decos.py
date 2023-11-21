"""Decorator source for Bank project"""
from functools import wraps
from exceptions import SessionError

def admin_required(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if self.user and getattr(self.user, 'is_admin', False):
            return func(self, *args, **kwargs)
        else:
            raise PermissionError('Permission Denied: You dont have required permissions to perform this operation!')
    return wrapper


def login_required(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if getattr(self, 'user', False):
            return func(self, *args, **kwargs)
        else:
            raise SessionError('SessionError: You should login for perform this operation (func.__name__). Please login !')
    return wrapper


def logout_required(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if getattr(self, 'user', None) is None:
            return func(self, *args, **kwargs)
        else:
            raise SessionError('SessionError: You should logout for perform this operation (func.__name__). Please logout !')
    return wrapper


def limit_by_second(second):
    
    def decorator(func):
        cached_data = None
        last_time_call = 0
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal last_time_call, cached_data
            if ((t := time.time()) - last_time_call) >= second:
                last_time_call = t
                cached_data = func(*args, **kwargs)
            
            return cached_data
        return wrapper
    return decorator        

"""Decorator source for Bank project"""
from functools import wraps

def admin_required(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if getattr(self, 'is_admin', False):
            return func(self, *args, **kwargs)
        else:
            raise PermissionError('Permission Denied: You dont have required permissions to perform this operation!')
    return wrapper
        
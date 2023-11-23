"""Decorator source for Bank project"""
from functools import wraps
from exceptions import SessionError
from time import sleep, time
from threading import Thread, Event
import sys

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




def _loading_process(text, timeout, process_ready_event):
    '''
    This method can be removed.
    '''
    elapsed_warning_shown_flag = False
    chars = r'/-\|'
    clear_len = len(text) + len('.../')
    start_time = time()
    i = 0

    while not process_ready_event.is_set():
        elapsed_time = time() - start_time
       
        if elapsed_time >= timeout and elapsed_warning_shown_flag == False:
            sys.stdout.write('\r' + ' ' * clear_len + '\r')
            sys.stdout.flush()
            print('Warning !: Process did not complete within the excepted time. Something is going wrong right now. Please try to restart the app.')
            elapsed_warning_shown_flag = True

        sys.stdout.write(f'\r{text}...{chars[(i % 4)]}')
        sys.stdout.flush()
        sleep(0.1)
        i += 1        
        
        sys.stdout.write(f'\r{text}...{chars[(i % 4)]}')
        sys.stdout.flush()
        sleep(0.1)
        i += 1
    sys.stdout.write('\r' + ' ' * clear_len + '\r')
    sys.stdout.flush()


def manage_loading(duration, text):
    '''
    This method can be removed.
    '''
    def decorator(func):
        start_time = time()
        chars = r'/-\|'

        @wraps(func)
        def wrapper(*args, **kwargs):
            process_ready_event = Event()
            loading_thread = Thread(target=_loading_process, 
                                    args=(text, duration, 
                                          process_ready_event
                                          )
                                    )
            loading_thread.start()
            result = func(*args, **kwargs)
            process_ready_event.set()
            loading_thread.join()
            return result
        return wrapper
    return decorator
            


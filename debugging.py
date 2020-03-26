"""Debugging and dev tools""""

from functools import wraps

def showArgs(func):
    """Print the actual arguments of the function."""
    
    @wraps
    def inner(*args, **kwargs):
        print(f"Positional args: {args}\nKeywords args: {kwargs}")
        return func(*args, **kwargs)

    return inner

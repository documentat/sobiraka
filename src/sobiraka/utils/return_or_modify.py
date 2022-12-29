from functools import wraps


def return_or_modify(func):
    @wraps(func)
    def wrapped(self, arg):
        result = func(self, arg)
        if result is not None:
            return result
        else:
            return arg
    return wrapped

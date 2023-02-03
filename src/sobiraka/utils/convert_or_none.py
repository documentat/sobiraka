from typing import Callable, TypeVar

T = TypeVar('T')
R = TypeVar('R')

def convert_or_none(func: Callable[[T], R], value: T) -> R | None:
    if value is not None:
        return func(value)
    return None
from asyncio import create_task
from functools import wraps
from typing import Callable, ParamSpec, TypeVar

from sobiraka.runtime import RT

P = ParamSpec('P')
T = TypeVar('T')
def do_once(func: Callable[P, T]) -> Callable[P, T]:
    @wraps(func)
    async def wrapped(*args, **kwargs):
        key = func, args, tuple(kwargs.items())
        try:
            return await RT.AWAITABLES[key]
        except KeyError:
            awaitable = RT.AWAITABLES[key] = create_task(func(*args, **kwargs))
            return await awaitable
        finally:
            del RT.AWAITABLES[key]
    return wrapped

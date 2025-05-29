from __future__ import annotations

from typing import Generic, TypeVar

from .preventableevent import PreventableEvent

K = TypeVar('K')
T = TypeVar('T')


class ProductiveEvent(PreventableEvent, Generic[T]):
    """
    An event whose wait() returns a useful result instead of just None.
    It can raise an exception, too, because it extends PreventableEvent.
    """

    def __init__(self):
        super().__init__()
        self.result: T | None = None

    def set(self):
        raise NotImplementedError

    def set_result(self, result: T):
        self.result = result
        super().set()

    async def wait(self) -> T:
        await super().wait()
        return self.result

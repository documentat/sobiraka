from typing import Sequence, TypeVar

T = TypeVar('T')

class UniqueList(list, Sequence[T]):
    def append(self, item: T):
        if item not in self:
            super().append(item)
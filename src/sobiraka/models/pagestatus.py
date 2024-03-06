from __future__ import annotations

from enum import Enum, auto


class PageStatus(Enum):
    INITIALIZE = auto()
    PREPARE = auto()
    PROCESS1 = auto()
    PROCESS2 = auto()
    PROCESS3 = auto()
    PROCESS4 = auto()

    FAILURE = auto()
    DEP_FAILURE = auto()
    VOL_FAILURE = auto()

    def __repr__(self):
        return f'{self.__class__.__name__}.{self.name}'

    def __lt__(self, other):
        assert isinstance(other, PageStatus)
        return self.value < other.value

    def __le__(self, other):
        assert isinstance(other, PageStatus)
        return self.value <= other.value

    @staticmethod
    def range(old: PageStatus, new: PageStatus) -> tuple[PageStatus, ...]:
        return tuple(s for s in PageStatus if old < s <= new)

    def is_failed(self) -> bool:
        return self in (PageStatus.FAILURE, PageStatus.DEP_FAILURE, PageStatus.VOL_FAILURE)

from __future__ import annotations

from abc import ABCMeta
from enum import Enum, auto


class Status(Enum):
    DISCOVER = auto()
    LOAD = auto()
    PARSE = auto()
    PROCESS1 = auto()
    PROCESS2 = auto()
    PROCESS3 = auto()
    PROCESS4 = auto()

    SOURCE_FAILURE = auto()
    PAGE_FAILURE = auto()
    DEP_FAILURE = auto()
    DOC_FAILURE = auto()

    def __repr__(self):
        return f'{self.__class__.__name__}.{self.name}'

    def __lt__(self, other):
        assert isinstance(other, Status)
        return self.value < other.value

    def __le__(self, other):
        assert isinstance(other, Status)
        return self.value <= other.value

    @staticmethod
    def range(old: Status, new: Status) -> tuple[Status, ...]:
        return tuple(s for s in Status if old < s <= new)

    @property
    def prev(self) -> Status:
        return Status(self.value - 1)

    @property
    def next(self) -> Status:
        return Status(self.value + 1)

    def is_failed(self) -> bool:
        return self in (Status.SOURCE_FAILURE, Status.PAGE_FAILURE,
                        Status.DEP_FAILURE, Status.DOC_FAILURE)


class ObjectWithStatus(metaclass=ABCMeta):
    @property
    def status(self) -> Status:
        return self.__dict__.get('status', Status.DISCOVER)

    @status.setter
    def status(self, status: Status):
        old_status = self.__dict__.get('status', Status.DISCOVER)
        try:
            match old_status.is_failed(), status.is_failed():
                case False, False:
                    assert old_status <= status
                case True, False:
                    assert False
                case True, True:
                    assert old_status == status
        except AssertionError as exc:
            raise ValueError(f'Cannot change status from {old_status.name} to {status.name}') from exc

        self.__dict__['status'] = status

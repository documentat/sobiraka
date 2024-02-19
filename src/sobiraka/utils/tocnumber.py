from __future__ import annotations

from typing import Iterable


class TocNumber:
    """
    A sequence of numbers suitable for enumerating pages, like 5.2, 5.3, and so on.
    """
    def __init__(self, *numbers: int):
        self._numbers: tuple[int, ...] = numbers

    def __iter__(self) -> Iterable[int]:
        return iter(self._numbers)

    def __len__(self) -> int:
        return len(self._numbers)

    def __bool__(self):
        return len(self._numbers) > 0

    def __eq__(self, other):
        return isinstance(other, TocNumber) and self._numbers == other._numbers

    def __hash__(self):
        return hash(self._numbers)

    def __str__(self):
        return self.format('{}')

    def __repr__(self):
        return f'<{self.__class__.__name__}: {self}>'

    def __add__(self, value: int) -> TocNumber:
        assert isinstance(value, int)
        return TocNumber(*self._numbers[:-1], self._numbers[-1] + value)

    def format(self, template: str) -> str:
        return template.format('.'.join(map(str, self._numbers)))

    def increased(self) -> TocNumber:
        return TocNumber(*self._numbers[:-1], self._numbers[-1] + 1)

    def increased_at(self, level: int) -> TocNumber:
        """
        Increase given level by one.
        If the counter had any values after the given level, they will be removed (e.g., 4.2.1→4.3).
        If the given level exceeds the current number of levels by more than one, an exception will be thrown.
        """
        n = level - 1
        if n < len(self._numbers):
            return TocNumber(*self._numbers[:n], self._numbers[n] + 1)
        if n == len(self._numbers):
            return TocNumber(*self._numbers, 1)
        raise ValueError(f'Can\'t increase level {level} in {str(self)!r}.')


class Unnumbered(TocNumber):
    def format(self, template: str) -> str:
        return ''

    def __repr__(self):
        return f'{self.__class__.__name__}()'


SKIP_NUMERATION = 'SKIP_NUMERATION'

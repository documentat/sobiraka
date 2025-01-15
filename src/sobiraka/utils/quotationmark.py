from enum import Enum
from typing import Self


class QuotationMark(Enum):
    STRAIGHT = 'straight'
    CURLY = 'curly'
    GUILLEMETS = 'guillemets'

    def __repr__(self):
        return f'{self.__class__.__name__}.{self.name}'

    @property
    def pair(self) -> str:
        return {
            QuotationMark.STRAIGHT: '""',
            QuotationMark.CURLY: '“”',
            QuotationMark.GUILLEMETS: '«»',
        }[self]

    @property
    def opening(self) -> str:
        return self.pair[0]

    @property
    def closing(self) -> str:
        return self.pair[1]

    @classmethod
    def by_char(cls, char: str) -> Self:
        for option in QuotationMark:
            if char in option.pair:
                return option
        raise ValueError(char)

    @classmethod
    def load_list(cls, names: str) -> tuple[Self, ...]:
        return tuple(map(QuotationMark, names.split('+')))

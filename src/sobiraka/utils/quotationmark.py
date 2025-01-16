import re
from enum import Enum
from typing import Self


class QuotationMark(Enum):
    ANGLED = '«»'
    CURVED_DOUBLE = '“”'
    CURVED_SINGLE = '‘’'
    LOW_DOUBLE = '„“'
    LOW_SINGLE = '‚’'
    STRAIGHT_DOUBLE = '""'
    STRAIGHT_SINGLE = "''"

    @classmethod
    def load_one(cls, name: str) -> Self:
        return {
            'Angled': QuotationMark.ANGLED,
            'CurvedDouble': QuotationMark.CURVED_DOUBLE,
            'CurvedSingle': QuotationMark.CURVED_SINGLE,
            'LowDouble': QuotationMark.LOW_DOUBLE,
            'LowSingle': QuotationMark.LOW_SINGLE,
            'StraightDouble': QuotationMark.STRAIGHT_DOUBLE,
            'StraightSingle': QuotationMark.STRAIGHT_SINGLE,
        }[name]

    @classmethod
    def regexp(cls) -> re.Pattern:
        return re.compile('[' + ''.join(qm.value for qm in QuotationMark) + ']')

    @classmethod
    def load_list(cls, names: str) -> tuple[Self, ...]:
        return tuple(map(QuotationMark.load_one, names))

    @classmethod
    def by_opening(cls, opening: str) -> Self:
        for option in QuotationMark:
            if opening in option.value:
                return option
        raise ValueError(opening)

    def __repr__(self):
        return f'{self.__class__.__name__}.{self.name}'

    @property
    def opening(self) -> str:
        return self.value[0]

    @property
    def closing(self) -> str:
        return self.value[1]

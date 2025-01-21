import re
from enum import Enum
from typing import Self, Sequence


class QuotationMark(Enum):
    ANGLED = '«»'
    CURVED_DOUBLE = '“”'
    CURVED_SINGLE = '‘’'
    GERMAN = '„“'
    STRAIGHT_DOUBLE = '""'
    STRAIGHT_SINGLE = "''"

    @classmethod
    def load_list(cls, names: Sequence[str]) -> tuple[Self, ...]:
        mapping = {
            'Angled': QuotationMark.ANGLED,
            'CurvedDouble': QuotationMark.CURVED_DOUBLE,
            'CurvedSingle': QuotationMark.CURVED_SINGLE,
            'German': QuotationMark.GERMAN,
            'StraightDouble': QuotationMark.STRAIGHT_DOUBLE,
            'StraightSingle': QuotationMark.STRAIGHT_SINGLE,
        }
        return tuple(mapping[name] for name in names)

    @classmethod
    def regexp(cls) -> re.Pattern:
        return re.compile('[' + ''.join(qm.value for qm in QuotationMark) + ']')

    @classmethod
    def by_opening(cls, opening: str) -> Self:
        for option in QuotationMark:
            if option.opening == opening:
                return option
        raise ValueError(opening)

    def __str__(self):
        return self.name.replace('_', ' ').capitalize() + 'quotation marks'

    def __repr__(self):
        return f'{self.__class__.__name__}.{self.name}'

    @property
    def opening(self) -> str:
        return self.value[0]

    @property
    def closing(self) -> str:
        return self.value[1]


class Apostrophe(Enum):
    CURVED = "’"
    STRAIGHT = "'"

    @classmethod
    def load(cls, name: str) -> Self:
        return {
            'Curved': Apostrophe.CURVED,
            'Straight': Apostrophe.STRAIGHT,
        }[name]

    @classmethod
    def regexp(cls) -> re.Pattern:
        return re.compile('[' + ''.join(a.value for a in Apostrophe) + ']')

    def __repr__(self):
        return f'{self.__class__.__name__}.{self.name}'

    @property
    def incompatible_quotation_marks(self) -> Sequence[QuotationMark]:
        return tuple(qm for qm in QuotationMark if self.value in qm.value)

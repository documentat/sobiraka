from dataclasses import dataclass
from typing import TYPE_CHECKING

from panflute import Element

from .pos import Pos

if TYPE_CHECKING:
    from .textmodel import TextModel


@dataclass(frozen=True)
class Fragment:
    """
    A specific fragment of text in a :class:`TextModel`,
    usually (but not necessarily) related to a single Panflute element.
    """

    tm: 'TextModel'
    """The model this fragments belong to. Used for getting the text representation."""

    start: Pos
    """The first character position."""

    end: Pos
    """The last character position."""

    element: Element | None = None
    """An optional reference to the element which contents this fragment represents."""

    def __repr__(self):
        return f'<[{self.start}-{self.end}] {self.text!r}>'

    def __hash__(self):
        return hash((id(self.tm), self.start, self.end))

    @property
    def text(self) -> str:
        if self.start == self.end:
            return ''

        if self.start.line == self.end.line:
            return self.tm.lines[self.start.line][self.start.char:self.end.char]

        result = self.tm.lines[self.start.line][self.start.char:]
        for line in range(self.start.line + 1, self.end.line):
            result += '\n' + self.tm.lines[line]
        result += '\n' + self.tm.lines[self.end.line][:self.end.char]
        return result

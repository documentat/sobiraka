from dataclasses import dataclass


@dataclass(frozen=True, eq=True, order=True)
class Pos:
    """
    An exact position of a character in a :class:`TextModel`.
    Consists of a line number and a character number within that line.
    """
    line: int
    char: int

    def __repr__(self):
        return f'{self.__class__.__name__}({self.line}, {self.char})'

    def __str__(self):
        return f'{self.line}:{self.char}'

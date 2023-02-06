from dataclasses import dataclass
from pathlib import Path


class Issue:
    pass


@dataclass(order=True, frozen=True)
class BadLink(Issue):
    target: str

    def __str__(self):
        return f'Bad link: {self.target}'


@dataclass(order=True, frozen=True)
class AmbiguosLink(Issue):
    target: str
    anchor: str

    def __str__(self):
        return f'Ambiguos link: {self.target}#{self.anchor}'


@dataclass(order=True, frozen=True)
class MisspelledWords(Issue):
    relative_path: Path
    words: tuple[str, ...]

    def __str__(self):
        return f'Misspelled words in {self.relative_path}: {", ".join(self.words)}.'
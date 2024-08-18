from dataclasses import dataclass
from textwrap import shorten

from sobiraka.utils import RelativePath


class Issue:
    pass


@dataclass(order=True, frozen=True)
class BadImage(Issue):
    target: str

    def __str__(self):
        return f'Image not found: {self.target}'


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
    path_in_project: RelativePath
    words: tuple[str, ...]

    def __str__(self):
        return f'Misspelled words in {self.path_in_project}: {", ".join(self.words)}.'


@dataclass(order=True, frozen=True)
class PhraseBeginsWithLowerCase(Issue):
    phrase: str

    def __str__(self):
        prefix = 'Phrase begins with a lowercase letter: '
        return prefix + shorten(self.phrase, 80 - len(prefix) - 1, placeholder="...")

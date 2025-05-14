from abc import ABCMeta
from dataclasses import dataclass
from textwrap import shorten

from sobiraka.utils import Apostrophe, QuotationMark, RelativePath


class Issue(metaclass=ABCMeta):
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

    def __repr__(self):
        return f'{self.__class__.__name__}({self.target!r})'


@dataclass(order=True, frozen=True)
class NonExistentFileInNav(Issue):
    relative_path: RelativePath

    def __str__(self):
        from sobiraka.models.source import NAV_FILENAME
        return f'{NAV_FILENAME} references a non-existing file: {self.relative_path}'


@dataclass(order=True, frozen=True)
class IndexFileInNav(Issue):
    relative_path: RelativePath

    def __str__(self):
        from sobiraka.models.source import NAV_FILENAME
        return f'{NAV_FILENAME} references an index file: {self.relative_path}'


@dataclass(order=True, frozen=True)
class MisspelledWords(Issue):
    path_in_project: RelativePath
    words: tuple[str, ...]

    def __str__(self):
        return f'Misspelled words: {", ".join(self.words)}.'


@dataclass(order=True, frozen=True)
class PhraseBeginsWithLowerCase(Issue):
    phrase: str

    def __str__(self):
        prefix = 'Phrase begins with a lowercase letter: '
        return prefix + shorten(self.phrase, 80 - len(prefix) - 1, placeholder="...")


@dataclass(frozen=True)
class MismatchingQuotationMarks(Issue):
    text: str

    def __str__(self):
        return shorten(f'Mismatching quotation marks: {self.text}', 120, placeholder='...')


@dataclass(frozen=True)
class UnclosedQuotationSpan(Issue):
    text: str

    def __str__(self):
        return shorten(f'Unclosed quotation mark: {self.text}', 120, placeholder='...')


@dataclass(frozen=True)
class IllegalQuotationMarks(Issue):
    nesting: tuple[QuotationMark, ...]
    text: str

    def __str__(self):
        if len(self.nesting) == 1:
            result = self.nesting[0].name.replace('_', ' ').capitalize() \
                     + ' quotation marks are not allowed here: ' + self.text
        else:
            result = 'Nesting order ' \
                     + ''.join(qm.opening for qm in self.nesting) \
                     + '…' \
                     + ''.join(qm.closing for qm in reversed(self.nesting)) \
                     + ' is not allowed here: ' + self.text
        return shorten(result, 120, placeholder='...')


@dataclass(frozen=True)
class UnexpectedClosingQuotationMark(Issue):
    text: str

    def __str__(self):
        result = 'Unexpected closing quotation mark: '
        result += shorten(self.text[::-1], 120 - len(result), placeholder='...')[::-1]
        return result


@dataclass(frozen=True)
class IllegalApostrophe(Issue):
    apostrophe: Apostrophe
    text: str

    def __str__(self):
        return f'{self.apostrophe.name.capitalize()} apostrophe is not allowed: {self.text}'

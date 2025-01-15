from dataclasses import dataclass
from textwrap import shorten

from sobiraka.utils import QuotationMark, RelativePath


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
        return shorten(f'Mismatching quotation marks: {self.text}', 72, placeholder='...')


@dataclass(frozen=True)
class UnclosedQuotationSpan(Issue):
    text: str

    def __str__(self):
        return shorten(f'Unclosed quotation mark: {self.text}', 72, placeholder='...')


@dataclass(frozen=True)
class IllegalQuotationMarks(Issue):
    nesting: tuple[QuotationMark, ...]
    text: str

    def __str__(self):
        chars = ''.join(qm.opening for qm in self.nesting) \
                + ''.join(qm.closing for qm in reversed(self.nesting))
        if len(self.nesting) > 1:
            text = f'Nesting order {chars} is not allowed: {self.text}'
        else:
            text = f'Quotation marks {chars} are not allowed: {self.text}'
        return shorten(text, 72, placeholder='...')

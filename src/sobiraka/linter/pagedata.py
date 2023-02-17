from __future__ import annotations

import re
from _bisect import bisect_left
from dataclasses import dataclass
from functools import cache, cached_property
from itertools import chain, pairwise
from typing import Iterable, Sequence

from sobiraka.models import Book, Page

SEP = re.compile(r'[?!.]+\s*')
END = re.compile(r'[?!.]+\s*$')


@dataclass
class PageData:
    page: Page
    text: str

    @property
    def lines(self) -> list[str]:
        return self.text.splitlines()

    @property
    def exceptions(self) -> Sequence[Fragment]:
        for exceptions in self.exceptions_by_line:
            return tuple(chain(*self.exceptions_by_line))

    @cached_property
    def exceptions_by_line(self) -> Sequence[Sequence[Fragment]]:
        exceptions_by_line: list[list[Fragment]] = []
        regexp = exceptions_regexp(self.page.book)
        for linenum, line in enumerate(self.lines):
            exceptions_by_line.append([])
            if regexp:
                for m in re.finditer(regexp, line):
                    exceptions_by_line[linenum].append(Fragment(self, linenum, m.start(), m.end()))
        return tuple(tuple(x) for x in exceptions_by_line)

    @cached_property
    def naive_phrases(self) -> Sequence[Sequence[Fragment]]:
        """
        Split each line into phrases by pediods, exclamation or question marks or clusters of them.
        The punctuation marks are included in the phrases, but the spaces after are not.

        Return pairs of numbers representing `start` and `end` of each phrase.
        The content of each phrase can then be accessed as `line[start:end]`.
        """
        result: list[list[Fragment]] = []

        for linenum, line in enumerate(self.lines):
            result.append([])

            separators = re.search('^', line), *re.finditer(SEP, line), re.search('$', line)

            for before, after in pairwise(separators):
                num_spaces = len(re.search(r'\s*$', after.group()).group())
                result[linenum].append(Fragment(self, linenum, before.end(), after.end() - num_spaces))

            if result[linenum][-1].text == '':
                result[linenum].pop()

        return tuple(tuple(x) for x in result)

    @cached_property
    def phrases(self) -> Sequence[Fragment]:
        """
        Normally, a text is split into phrases by periods, exclamation points, etc.
        However, the 'exceptions' dictionary may contain some words
        that contain periods in them ('e.g.', 'H.265', 'www.example.com').
        This function first splits the line into phrases using :meth:`phrase_bounds()`,
        but then moves their bounds for each exception that was accidentally split.

        If `remove_exceptions=True`, the exceptions will be replaced with spaces in the result.
        This is used to generate phrases that can be sent to another linter.
        """
        result: list[Fragment] = []

        # Each phrase can only be on a single line,
        # so we work with each line separately
        for linenum, line in enumerate(self.lines):
            phrases = list(self.naive_phrases[linenum])
            exceptions = self.exceptions_by_line[linenum]

            for exc in exceptions:
                # Find the phrases overlapping with the exception from left and right.
                left = bisect_left(phrases, exc.start, key=lambda x: x.end)
                right = bisect_left(phrases, exc.end, key=lambda x: x.start) - 1

                # If the exception ends like a phrase would (e.g., 'e.g.'),
                # we will merge one more phrase from the right.
                # Unless, of course, there are no more phrases on the right.
                if re.search(END, exc.text):
                    right = min(right + 1, len(phrases) - 1)

                # Merge the left and right phrases into one.
                # (If left and right are the same phrase, this does nothing.)
                # Example:
                #     Example Corp. | is a company. | Visit www. | example. | com for more info.
                #   → Example Corp. is a company. | Visit www.example.com for more info.
                phrases[left:right + 1] = Fragment(self, linenum, phrases[left].start, phrases[right].end),

            # Add this line's phrases to the result
            result += phrases

        return tuple(result)

    @property
    def clean_phrases(self) -> Iterable[str]:
        for phrase in self.phrases:
            result = phrase.text
            for exc in self.exceptions_by_line[phrase.linenum]:
                if phrase.start <= exc.start and exc.end <= phrase.end:
                    start = exc.start - phrase.start
                    end = exc.end - phrase.start
                    result = result[:start] + ' ' * len(exc.text) + result[end:]
            yield result


@dataclass(frozen=True)
class Fragment:
    page_data: PageData
    linenum: int
    start: int
    end: int

    def __repr__(self):
        return f'<{self.linenum} {self.start} {self.end}: {self.text!r}>'

    @property
    def text(self) -> str:
        return self.page_data.lines[self.linenum][self.start:self.end]


@cache
def exceptions_regexp(book: Book) -> re.Pattern | None:
    """
    Prepare a regular expression that matches any exception.
    If no exceptions are provided, returns `None`.
    """
    regexp_parts: list[str] = []
    for exceptions_path in book.lint.exceptions:
        with exceptions_path.open() as exceptions_file:
            for line in exceptions_file:
                line = line.strip()
                if exceptions_path.suffix == '.regexp':
                    regexp_parts.append(line)
                else:
                    regexp_parts.append(r'\b' + re.escape(line) + r'\b')
    if regexp_parts:
        return re.compile('|'.join(regexp_parts))
from __future__ import annotations

import re
from bisect import bisect_left
from dataclasses import dataclass, field
from functools import cached_property
from itertools import chain, pairwise
from typing import Iterable, Sequence

from panflute import Element

SEP = re.compile(r'[?!.]+\s*')
END = re.compile(r'[?!.]+\s*$')


@dataclass
class TextModel:
    lines: list[str] = field(default_factory=lambda: [''])
    fragments: list[Fragment] = field(default_factory=list)
    exceptions_regexp: re.Pattern | None = None

    @property
    def text(self) -> str:
        return '\n'.join(self.lines)

    @property
    def end_pos(self) -> Pos:
        return Pos(len(self.lines) - 1, len(self.lines[-1]))

    @cached_property
    def exceptions_by_line(self) -> Sequence[Sequence[Fragment]]:
        exceptions_by_line: list[list[Fragment]] = []
        for linenum, line in enumerate(self.lines):
            exceptions_by_line.append([])
            if self.exceptions_regexp:
                for m in re.finditer(self.exceptions_regexp, line):
                    exceptions_by_line[linenum].append(Fragment(self,
                                                                Pos(linenum, m.start()),
                                                                Pos(linenum, m.end())))
        return tuple(tuple(x) for x in exceptions_by_line)

    @property
    def exceptions(self) -> Sequence[Fragment]:
        return tuple(chain(*self.exceptions_by_line))

    @cached_property
    def naive_phrases(self) -> Sequence[Sequence[Fragment]]:
        """
        Split each line into phrases by periods, exclamation or question marks or clusters of them.
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
                result[linenum].append(Fragment(self,
                                                Pos(linenum, before.end()),
                                                Pos(linenum, after.end() - num_spaces)))

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
        for linenum in range(len(self.lines)):
            phrases = list(self.naive_phrases[linenum])
            exceptions = self.exceptions_by_line[linenum]

            for exc in exceptions:
                # Find the phrases overlapping with the exception from left and right.
                left = bisect_left(phrases, exc.start.char, key=lambda x: x.end.char)
                right = bisect_left(phrases, exc.end.char, key=lambda x: x.start.char) - 1

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
                phrases[left:right + 1] = (Fragment(self, phrases[left].start, phrases[right].end),)

            # Add this line's phrases to the result
            result += phrases

        return tuple(result)

    @property
    def clean_phrases(self) -> Iterable[str]:
        for phrase in self.phrases:
            result = phrase.text
            for exc in self.exceptions_by_line[phrase.start.line]:
                if phrase.start <= exc.start and exc.end <= phrase.end:
                    start = exc.start.char - phrase.start.char
                    end = exc.end.char - phrase.start.char
                    result = result[:start] + ' ' * len(exc.text) + result[end:]
            yield result


@dataclass(frozen=True)
class Fragment:
    tm: TextModel
    start: Pos
    end: Pos
    element: Element | None = None

    def __repr__(self):
        return f'<[{self.start}-{self.end}] {self.text!r}>'

    def __hash__(self):
        return hash((id(self.tm), self.start, self.end))

    @property
    def text(self) -> str:
        if self.start.line == self.end.line:
            return self.tm.lines[self.start.line][self.start.char:self.end.char]

        result = self.tm.lines[self.start.line][self.start.char:]
        for line in range(self.start.line+1, self.end.line):
            result += '\n' + self.tm.lines[line]
        result += '\n' + self.tm.lines[self.end.line][:self.end.char]
        return result


@dataclass(frozen=True, eq=True, order=True)
class Pos:
    line: int
    char: int

    def __repr__(self):
        return f'{self.__class__.__name__}({self.line}, {self.char})'

    def __str__(self):
        return f'{self.line}:{self.char}'

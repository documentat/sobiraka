from __future__ import annotations

import re
from bisect import bisect_left
from dataclasses import dataclass, field
from itertools import pairwise
from typing import Sequence

from panflute import Element

from sobiraka.models import Anchor
from sobiraka.utils import update_last_dataclass

SEP = re.compile(r'[?!.]+\s*')
END = re.compile(r'[?!.]+\s*$')


@dataclass(kw_only=True)
class TextModel:
    """
    Information about a Page's text.

    Some methods here are only available after you finish editing `lines`, `fragments` and `sections`
    and call `freeze()`.
    """

    lines: list[str] = field(default_factory=lambda: [''])
    """
    Lines of plain text.
    
    The lines do not have to match the lines in the source code, but they must not change once added.
    Other properties and methods, such as `end_pos` and `exceptions`,
    indirectly reference both the lines numeration and their content, see :class:`Pos`.
    """

    fragments: list[Fragment] = field(default_factory=list, init=False)
    """
    List of text fragments, usually related to specific elements.
    
    In :class:`Prover`, this is used to quickly find the first element in a phrase.
    """

    sections: dict[Anchor | None, Fragment] = field(default_factory=dict, init=False)
    """
    Information about how the page is split into sections by headers.
    
    A page without headers (except for H1) will have just one section under the key `None`.
    Otherwise, each new header will end the previous section and start a new one.
    
    The header itself is never included into the :class:`Fragment` representing its section.
    """

    exceptions_regexp: re.Pattern | None = field(default=None)
    """
    The regular expression what will be used for finding `exceptions`.
    Should be loaded from the volume's configuration.
    """

    __frozen: bool = field(default=False, init=False)

    def freeze(self):
        """
        Call this to indicate that you are not going to modify `lines`, `fragments` and `sections` anymore.
        You must call this to be able to use some other methods.
        """
        self.__frozen = True

    @property
    def text(self) -> str:
        """
        The plain text representation of the whole page.
        """
        return '\n'.join(self.lines)

    @property
    def end_pos(self) -> Pos:
        """
        A :class:`Pos` that points to the end of the last line.
        """
        if len(self.lines) == 0:
            return Pos(0, 0)
        return Pos(len(self.lines) - 1, len(self.lines[-1]))

    def exceptions(self) -> Sequence[Sequence[Fragment]]:
        """
        Find positions of all words or word combinations that match the :data:`exceptions_regexp`.

        The result will contain one sequence per each line in :data:`lines`,
        each sequence containing :class:`Fragment` objects indicating where the exceptions are found.
        """
        assert self.__frozen

        exceptions: list[list[Fragment]] = []
        for linenum, line in enumerate(self.lines):
            exceptions.append([])
            if self.exceptions_regexp:
                for m in re.finditer(self.exceptions_regexp, line):
                    exceptions[linenum].append(Fragment(self,
                                                        Pos(linenum, m.start()),
                                                        Pos(linenum, m.end())))
        return tuple(tuple(x) for x in exceptions)

    def naive_phrases(self) -> Sequence[Sequence[Fragment]]:
        """
        Split each line into phrases by periods, exclamation or question marks or clusters of them.
        The punctuation marks are included in the phrases, but the spaces after are not.

        This is called `naive_phrases` because this is just the first step used by the real `phrases`
        which takes :data:`exceptions` into consideration and provides more reliable results.
        """
        assert self.__frozen

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

    def phrases(self) -> Sequence[Fragment]:
        """
        Normally, a text is split into phrases by periods, exclamation points, etc.
        However, the 'exceptions' dictionary may contain some words
        that contain periods in them ('e.g.', 'H.265', 'www.example.com').
        This function first calls `naive_phrases()` and then moves the phrase bounds
        for each exception that was accidentally split.
        """
        assert self.__frozen

        result: list[Fragment] = []

        naive_phrases = self.naive_phrases()
        exceptions = self.exceptions()

        # Each phrase can only be on a single line,
        # so we work with each line separately
        for linenum in range(len(self.lines)):
            phrases = list(naive_phrases[linenum])

            for exc in exceptions[linenum]:
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

    def sections_up_to_level(self, max_level: int) -> dict[Anchor | None, Fragment]:
        result: dict[Anchor | None, Fragment] = {}
        for anchor, fragment in self.sections.items():
            level = anchor.level if anchor is not None else 1
            if level <= max_level:
                result[anchor] = fragment
            else:
                update_last_dataclass(result, end=fragment.end)
        return result


@dataclass(frozen=True)
class Fragment:
    """
    A specific fragment of text in a :class:`TextModel`,
    usually (but not necessarily) related to a single Panflute element.
    """

    tm: TextModel
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

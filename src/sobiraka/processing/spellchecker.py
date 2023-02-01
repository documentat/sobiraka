import os
import os
import re
import sys
from asyncio import create_subprocess_exec, gather
from bisect import bisect_left
from collections import defaultdict
from functools import cached_property
from itertools import pairwise
from subprocess import PIPE
from typing import AsyncIterable, Awaitable, Iterable

from more_itertools import unique_everseen

from sobiraka.models import Book, Page
from sobiraka.runtime import RT
from .abstract import Plainifier

SEP = re.compile(r'[?!.]+\s*')
END = re.compile(r'[?!.]+\s*$')


class SpellChecker(Plainifier):

    def __init__(self, book: Book):
        super().__init__(book)

        self.misspelled_words: dict[Page, list[str]] = defaultdict(list)

        self.environ = os.environ
        if self.book.spellcheck.dictionaries:
            self.environ = self.environ.copy()
            self.environ['DICPATH'] = ':'.join((
                str(RT.FILES / 'dictionaries'),
                str(self.book.paths.manifest_path.parent)))
            self.environ['DICTIONARY'] = ','.join(self.book.spellcheck.dictionaries)

    async def run(self):
        tasks: list[Awaitable] = []
        for page in self.book.pages:
            tasks.append(self.check_page(page))
        await gather(*tasks)

        if self.misspelled_words:
            for page, words in sorted(self.misspelled_words.items()):
                print(f'Misspelled words in {page.relative_path}: {", ".join(words)}', file=sys.stderr)
            return 1

        return 0

    async def check_page(self, page: Page):
        words: list[str] = []
        for phrase in await self.phrases(page, remove_exceptions=True):
            words += phrase.split()
        words = list(unique_everseen(words))

        async for misspelled_word in self.find_misspelled_words(words):
            if misspelled_word not in self.misspelled_words[page]:
                self.misspelled_words[page].append(misspelled_word)

    @cached_property
    def exceptions(self) -> tuple[tuple[str, ...], tuple[str, ...]]:
        exception_texts: list[str] = []
        exception_regexps: list[str] = []

        for exceptions_path in self.book.spellcheck.exceptions:
            with exceptions_path.open() as exceptions_file:
                if exceptions_path.suffix == '.regexp':
                    exception_regexps += (line.strip() for line in exceptions_file)
                else:
                    exception_texts += (line.strip() for line in exceptions_file)

        return tuple(exception_texts), tuple(exception_regexps)

    @cached_property
    def exceptions_regexp(self) -> re.Pattern | None:
        """
        Prepare a regular expression that matches any exception.
        If no exceptions are provided, returns `None`.
        """
        regexp_parts = list(self.exceptions[1])
        for exception in self.exceptions[0]:
            regexp_parts.append(r'\b' + re.escape(exception) + r'\b')
        return re.compile('|'.join(regexp_parts)) if regexp_parts else None

    async def phrases(self, page: Page, *, remove_exceptions: bool = False) -> tuple[str, ...]:
        """
        Normally, a text is split into phrases by periods, exclamation points, etc.
        However, the 'exceptions' dictionary may contain some words
        that contain periods in them ('e.g.', 'H.265', 'www.example.com').
        This function first splits the line into phrases using :meth:`phrase_bounds()`,
        but then moves their bounds for each exception that was accidentally split.

        If `remove_exceptions=True`, the exceptions will be replaced with spaces in the result.
        This is used to generate phrases that can be sent to another linter.
        """
        text = await self.plainify(page)

        phrases: list[str] = []

        # Each phrase can only be on a single line,
        # so we work with each line separately
        for line in text.splitlines():

            # Split the line into phrases, but then move their bounds
            # for each exception that was accidentally split.
            # Example:
            #     Example Corp. is a company. Visit www.example.com for more info.
            #   → Example Corp. | is a company. | Visit www. | example. | com for more info.
            # BTW, if you are debugging this function, here is a useful expression for you:
            #   list(line[start:end] for start,end in bounds)
            bounds = self.phrase_bounds(line)

            # Look for exceptions
            for m in re.finditer(self.exceptions_regexp, line):
                exception: str = m.group()

                # Find the phrases overlapping with the exception from left and right.
                left = bisect_left(bounds, m.start(), key=lambda x: x[1])
                right = bisect_left(bounds, m.end(), key=lambda x: x[0]) - 1

                # If the exception ends like a phrase would, we will merge one more phrase from the right.
                # Unless, of course, there are no more phrases on the right.
                if re.search(END, exception):
                    right = min(right + 1, len(bounds) - 1)

                # Merge the left and right phrases into one.
                # (If left and right are the same phrase, this does nothing.)
                # Example:
                #     Example Corp. | is a company. | Visit www. | example. | com for more info.
                #   → Example Corp. is a company. | Visit www.example.com for more info.
                bounds[left:right+1] = (bounds[left][0], bounds[right][1]),

                # Optionally, replace the exception itself with spaces.
                if remove_exceptions:
                    line = line[:m.start()] + ' ' * len(m.group()) + line[m.end():]

            # Finally, add the phrases as strings to the result
            phrases += (line[start:end] for start, end in bounds)

        return tuple(filter(None, phrases))

    @staticmethod
    def phrase_bounds(line: str) -> list[tuple[int, int]]:
        """
        Split the line into phrase by pediods, exclamation or question marks or clusters of them.
        The punctuation marks are included in the phrases, but the spaces after are not.

        Return pairs of numbers representing `start` and `end` of each phrase.
        The content of each phrase can then be accessed as `line[start:end]`.
        """
        phrase_bounds: list[tuple[int, int]] = []

        separators = \
            re.search('^', line), \
            *re.finditer(SEP, line), \
            re.search('$', line)

        for before, after in pairwise(separators):
            num_spaces = len(re.search(r'\s*$', after.group()).group())
            phrase_bounds.append((before.end(), after.end() - num_spaces))

        if line[phrase_bounds[-1][0]:phrase_bounds[-1][1]] == '':
            phrase_bounds.pop()

        return phrase_bounds

    async def find_misspelled_words(self, words: Iterable[str]) -> AsyncIterable[str]:
        hunspell = await create_subprocess_exec(
            'hunspell',
            env=self.environ,
            stdin=PIPE,
            stdout=PIPE)
        hunspell_version = await hunspell.stdout.readline()
        assert re.match(br'Hunspell 1\..+\n', hunspell_version), hunspell_version

        hunspell.stdin.write(' '.join(words).encode('utf-8'))
        hunspell.stdin.close()

        async for line in hunspell.stdout:
            line = line.decode('utf-8').rstrip('\n')

            if m := re.fullmatch('& (\S+) (\d+) (\d+): (.+)', line):
                misspelled_word, near_misses_count, position, near_misses = m.groups()
                yield misspelled_word

            elif m := re.fullmatch('# (\S+) (\d+)', line):
                misspelled_word, position = m.groups()
                yield misspelled_word

            elif m := re.fullmatch('\+ (\w+)', line):
                continue

            elif line in ('', '*', '-'):
                continue

            else:
                raise ValueError(line)
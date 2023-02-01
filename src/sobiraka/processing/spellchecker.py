import os
import re
import sys
from asyncio import create_subprocess_exec, gather
from collections import defaultdict
from functools import cache
from itertools import chain, pairwise
from subprocess import PIPE
from typing import AsyncIterable, Awaitable, Iterable

from more_itertools import unique_everseen

from sobiraka.models import Book, Page
from sobiraka.runtime import RT
from .abstract import Plainifier


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
        for phrase in await self.get_phrases(page):
            words += phrase.split()
        words = list(unique_everseen(words))

        async for misspelled_word in self.find_misspelled_words(words):
            if misspelled_word not in self.misspelled_words[page]:
                self.misspelled_words[page].append(misspelled_word)

    @cache
    def get_exceptions(self) -> tuple[tuple[str, ...], tuple[str, ...]]:
        exception_texts: list[str] = []
        exception_regexps: list[str] = []

        for exceptions_path in self.book.spellcheck.exceptions:
            with exceptions_path.open() as exceptions_file:
                if exceptions_path.suffix == '.regexp':
                    exception_regexps += (line.strip() for line in exceptions_file)
                else:
                    exception_texts += (line.strip() for line in exceptions_file)

        return tuple(exception_texts), tuple(exception_regexps)

    async def get_phrases(self, page: Page) -> tuple[str, ...]:
        text = await self.plainify(page)

        phrases: list[str] = []

        # Normally, periods preak text into phrases.
        # However, the 'exceptions' dictionary may contain some words
        # that contain periods in them (e.g., 'e.g.', 'H.265', 'www.example.com').
        # Here, we are preparing a regular expression for searching such words.
        # We precompile it to speed up things.
        # Also, we skip any exceptions without periods to speed up things.
        exception_texts, exception_regexps = self.get_exceptions()
        exception_texts = tuple(filter(lambda x: '.' in x, exception_texts))
        exception_regexps = tuple(filter(lambda x: '.' in x, exception_regexps))
        if exception_texts or exception_regexps:
            regexp = re.compile('|'.join(chain(
                exception_regexps,
                map(re.escape, exception_texts),
            )))
        else:
            regexp = None

        # Each phrase can only be on a single line, so first split text into lines
        for line in text.splitlines():
            # The easy way, when there are no exceptions:
            # split the line by periods, remove empty phrases.
            if regexp is None:
                phrases += filter(None, (phrase.strip() for phrase in line.split('.')))

            # The hard way, with exceptions_regexp:
            # split the line by periods, but then move their bounds if an exception is found.
            else:
                # Split the line into phrases by periods.
                # For each phrase, remember its start and end positions.
                phrase_bounds: list[tuple[int, int]] = []
                periods = list(m.start() for m in re.finditer(r'\.+', line))
                for start, end in pairwise((0, *periods, len(line))):
                    phrase_bounds.append((start, end))

                # Look for exceptions
                for m in re.finditer(regexp, line):
                    left, right = None, None

                    # Find the phrase whose end overlaps with the exception
                    # and move its end so that it doesn't.
                    # Example:
                    #     ['Go to www', 'example', 'com for details']
                    #   → ['Go to', 'example', 'com for details']
                    for i in range(len(phrase_bounds)):
                        phrase_start, phrase_end = phrase_bounds[i]
                        if phrase_end >= m.start():
                            phrase_bounds[i] = phrase_start, m.start()
                            left = i
                            break

                    # Find the phrase whose start overlaps with the exception
                    # and move its start so that it doesn't.
                    # Example:
                    #     ['Go to', 'example', 'com for details']
                    #   → ['Go to', 'example', 'for details']
                    for i in reversed(range(len(phrase_bounds))):
                        phrase_start, phrase_end = phrase_bounds[i]
                        if phrase_start <= m.end():
                            phrase_bounds[i] = m.end(), phrase_end
                            right = i
                            break

                    # Remove the phrases completely included into the exception, if any.
                    # Example:
                    #     ['Go to', 'example', 'for details']
                    #   → ['Go to', 'for details']
                    del phrase_bounds[left+1:right]

                # Finally, add the phrases as strings to the result
                for start, end in phrase_bounds:
                    phrases.append(line[start:end].strip(' .'))

        return tuple(filter(None, phrases))

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
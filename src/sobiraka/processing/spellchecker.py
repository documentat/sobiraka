import os
import re
import sys
from asyncio import create_subprocess_exec, gather
from collections import defaultdict
from functools import cache
from itertools import pairwise
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
    def get_exceptions(self) -> list[str]:
        exceptions: list[str] = []
        for exceptions_path in self.book.spellcheck.exceptions:
            with exceptions_path.open() as exceptions_file:
                exceptions += (line.strip() for line in exceptions_file)
        return exceptions

    async def get_phrases(self, page: Page) -> list[str]:
        text = await self.plainify(page)

        phrases: list[str] = []

        for line in text.splitlines():

            phrase_bounds: list[tuple[int, int]] = []
            periods = list(m.start() for m in re.finditer(r'\.', line))
            for start, end in pairwise((0, *periods, len(line))):
                phrase_bounds.append((start, end))

            if exceptions_regexp := re.compile('|'.join(self.get_exceptions())):
                for m in re.finditer(exceptions_regexp, line):
                    left, right = None, None
                    for i in range(len(phrase_bounds)):
                        phrase_start, phrase_end = phrase_bounds[i]
                        if phrase_end >= m.start():
                            phrase_bounds[i] = phrase_start, m.start()
                            left = i
                            break
                    for i in reversed(range(len(phrase_bounds))):
                        phrase_start, phrase_end = phrase_bounds[i]
                        if phrase_start <= m.end():
                            phrase_bounds[i] = m.end(), phrase_end
                            right = i
                            break
                    del phrase_bounds[left+1:right]

            for start, end in phrase_bounds:
                phrases.append(line[start:end].strip(' .'))

        phrases = list(filter(None, phrases))
        return phrases

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
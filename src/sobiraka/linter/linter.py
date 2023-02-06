import os
import re
from asyncio import create_subprocess_exec, gather
from subprocess import PIPE
from typing import AsyncIterable, Awaitable, Iterable

from more_itertools import unique_everseen

from sobiraka.models import Book, MisspelledWords, Page
from sobiraka.processing.abstract import Plainifier
from sobiraka.runtime import RT
from .pagedata import PageData


class Linter(Plainifier):

    def __init__(self, book: Book):
        super().__init__(book)

        self._page_data: dict[Page, PageData] = {}

        self.environ = os.environ
        if self.book.lint.dictionaries:
            self.environ = self.environ.copy()
            self.environ['DICPATH'] = ':'.join((
                str(RT.FILES / 'dictionaries'),
                str(self.book.paths.manifest_path.parent)))
            self.environ['DICTIONARY'] = ','.join(self.book.lint.dictionaries)

    async def data(self, page: Page) -> PageData:
        if page not in self._page_data:
            text = await self.plainify(page)
            self._page_data[page] = PageData(page, text)
        return self._page_data[page]

    async def check(self):
        tasks: list[Awaitable] = []
        for page in self.book.pages:
            tasks.append(self.check_page(page))
        await gather(*tasks)

        if self.issues:
            return 1
        return 0

    async def check_page(self, page: Page):
        data = await self.data(page)

        words: list[str] = []
        for phrase in data.clean_phrases:
            words += phrase.split()
        words = list(unique_everseen(words))
        misspelled_words: list[str] = []
        async for word in self.find_misspelled_words(words):
            if word not in misspelled_words:
                misspelled_words.append(word)
        if misspelled_words:
            self.issues[page].add(MisspelledWords(page.relative_path, tuple(misspelled_words)))

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
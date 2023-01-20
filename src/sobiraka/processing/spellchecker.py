import os
import re
import sys
from asyncio import create_subprocess_exec, gather
from collections import defaultdict
from subprocess import PIPE
from typing import Awaitable

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
        txt = await self.plainify(page)

        hunspell = await create_subprocess_exec(
            'hunspell',
            env=self.environ,
            stdin=PIPE,
            stdout=PIPE)
        hunspell_version = await hunspell.stdout.readline()
        assert re.match(br'Hunspell 1\..+\n', hunspell_version), hunspell_version

        hunspell.stdin.write(txt.encode('utf-8'))
        hunspell.stdin.close()

        async for line in hunspell.stdout:
            line = line.decode('utf-8').rstrip('\n')

            if m := re.fullmatch('& (\S+) (\d+) (\d+): (.+)', line):
                misspelled_word, near_misses_count, position, near_misses = m.groups()
                if misspelled_word not in self.misspelled_words[page]:
                    self.misspelled_words[page].append(misspelled_word)

            elif m := re.fullmatch('# (\S+) (\d+)', line):
                misspelled_word, position = m.groups()
                if misspelled_word not in self.misspelled_words[page]:
                    self.misspelled_words[page].append(misspelled_word)

            elif m := re.fullmatch('\+ (\w+)', line):
                continue

            elif line in ('', '*', '-'):
                continue

            else:
                raise ValueError(line)
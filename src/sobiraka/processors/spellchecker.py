import os
import re
import sys
from asyncio import as_completed, create_subprocess_exec, create_task, gather, Queue, Task
from subprocess import PIPE
from typing import Awaitable

from panflute import Link, Para, Str, stringify

from sobiraka.building.processor import Processor
from sobiraka.models import Book, Page
from sobiraka.runtime import RT

_NUM_WORKERS = 4
_SEPARATOR = 'JJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJ'


class SpellChecker(Processor):

    def __init__(self, book: Book):
        super().__init__(book)

        self.running: bool = True
        self.lines: dict[Page, list[str]] = {}
        self.queue: Queue[Page | None] = Queue()
        self.misspelled_words: dict[Page, set[str]] = {}

    async def run(self) -> int:

        workers: list[Task] = []
        for i in range(_NUM_WORKERS):
            workers.append(create_task(self.worker()))

        tasks: list[Awaitable] = []
        for page in self.book.pages:
            self.lines[page] = []
            tasks.append(self.process1(page))

        for future in as_completed(tasks):
            page = await future
            await self.queue.put(page)

        await self.queue.put(None)
        await gather(*workers)

        if self.misspelled_words:
            for page, words in sorted(self.misspelled_words.items()):
                print(f'Misspelled words in {page.relative_path}: {", ".join(sorted(words))}', file=sys.stderr)
            return 1

        return 0

    async def worker(self):
        environ = os.environ
        if self.book.spellcheck.dictionaries:
            environ = environ.copy()
            environ['DICPATH'] = str(RT.FILES / 'dictionaries') + ':' + str(self.book.root)
            environ['DICTIONARY'] = ','.join(self.book.spellcheck.dictionaries)
        hunspell = await create_subprocess_exec('hunspell', '-i', 'utf-8', env=environ, stdin=PIPE, stdout=PIPE)

        hunspell_version = await hunspell.stdout.readline()
        assert re.match(br'Hunspell 1\..+\n', hunspell_version), hunspell_version

        while self.running:
            page = await self.queue.get()
            if page is None:
                self.running = False
                break

            text = '\n'.join(self.lines[page]) + '\n' + _SEPARATOR + '\n'
            hunspell.stdin.write(text.encode('utf-8'))

            while True:
                line = await hunspell.stdout.readline()
                line = line.decode('utf-8').rstrip('\n')

                if m := re.fullmatch('& (\S+) (\d+) (\d+): (.+)', line):
                    misspelled_word, near_misses_count, position, near_misses = m.groups()
                    self.misspelled_words.setdefault(page, set()).add(misspelled_word)

                elif m := re.fullmatch('# (\S+) (\d+)', line):
                    misspelled_word, position = m.groups()
                    if misspelled_word == _SEPARATOR:
                        break
                    self.misspelled_words.setdefault(page, set()).add(misspelled_word)

                elif m := re.fullmatch('\+ (\w+)', line):
                    continue

                elif line in ('', '*', '-'):
                    continue

                else:
                    raise ValueError(line)

    ################################################################################

    async def process_link(self, elem: Link, page: Page):
        self.lines[page].append(elem.title)
        await self.process_element(elem.content, page)

    async def process_para(self, elem: Para, page: Page):
        self.lines[page].append(stringify(elem))

    async def process_str(self, elem: Str, page: Page):
        self.lines[page].append(elem.text)

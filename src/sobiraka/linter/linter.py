from asyncio import gather
from typing import Awaitable

from more_itertools import unique_everseen

from sobiraka.models import Book, MisspelledWords, Page
from sobiraka.processing.abstract import Plainifier
from .hunspell import run_hunspell
from .pagedata import PageData


class Linter(Plainifier):

    def __init__(self, book: Book):
        super().__init__(book)
        self._page_data: dict[Page, PageData] = {}

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
        async for word in run_hunspell(words, self.book):
            if word not in misspelled_words:
                misspelled_words.append(word)
        if misspelled_words:
            self.issues[page].add(MisspelledWords(page.relative_path, tuple(misspelled_words)))
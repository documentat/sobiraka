from asyncio import gather
from inspect import getfile
from pathlib import Path
from unittest import IsolatedAsyncioTestCase

from sobiraka.processors import PdfBuilder
from sobiraka.models import Book


class BookTestCase(IsolatedAsyncioTestCase):
    maxDiff = None

    async def asyncSetUp(self):
        filepath = Path(getfile(self.__class__))
        self.dir: Path = filepath.parent

        book_yaml = self.dir / f'{filepath.stem}.yaml'
        self.book = await Book.from_manifest(book_yaml)

        self.processor = PdfBuilder(self.book)  # TODO make a simpler processor

        awaitables = tuple(self.processor.process2(page) for page in self.book.pages)
        await gather(*awaitables)

    def test_errors(self):
        for page in self.book.pages:
            with self.subTest(page.relative_path.with_suffix('')):
                self.assertEqual(page.errors, set())
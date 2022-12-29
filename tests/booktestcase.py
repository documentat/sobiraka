from asyncio import gather
from inspect import getfile
from pathlib import Path
from unittest import IsolatedAsyncioTestCase, load_tests, TestLoader, TestSuite

from sobiraka.models import Book


class BookTestCase(IsolatedAsyncioTestCase):
    maxDiff = None

    async def asyncSetUp(self):
        filepath = Path(getfile(self.__class__))
        self.dir: Path = filepath.parent

        book_yaml = self.dir / f'{filepath.stem}.yaml'
        self.book = await Book.from_manifest(book_yaml)

        awaitables = tuple(page.processed2.wait() for page in self.book.pages)
        await gather(*awaitables)

    def test_errors(self):
        for page in self.book.pages:
            with self.subTest(page.relative_path.with_suffix('')):
                self.assertEqual(page.errors, set())
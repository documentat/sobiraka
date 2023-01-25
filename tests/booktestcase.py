from asyncio import gather
from functools import cached_property
from inspect import getfile
from pathlib import Path
from typing import Any, Generic, TypeVar
from unittest import IsolatedAsyncioTestCase

from sobiraka.models import Book, Page
from sobiraka.processing.abstract import Plainifier, Processor

T = TypeVar('T', bound=Processor)


class BookTestCase:
    class Base(IsolatedAsyncioTestCase, Generic[T]):
        maxDiff = None

        async def asyncSetUp(self):
            filepath = Path(getfile(self.__class__))
            self.dir: Path = filepath.parent

            book_yaml = self.dir / f'{filepath.stem}.yaml'
            self.book = Book.from_manifest(book_yaml)

            awaitables = tuple(self.processor.process2(page) for page in self.book.pages)
            await gather(*awaitables)

        @cached_property
        def processor(self) -> T:
            return Plainifier(self.book)

        def subTest(self, msg: Any = ..., **params: Any):
            match msg:
                case Page() as page:
                    return super().subTest(page.relative_path.with_suffix(''))
                case _:
                    return super().subTest(msg)

        def test_errors(self):
            for page in self.book.pages:
                with self.subTest(page):
                    self.assertEqual(page.errors, set())
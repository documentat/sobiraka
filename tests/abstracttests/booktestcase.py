from asyncio import gather
from difflib import unified_diff
from functools import cached_property
from inspect import getfile
from pathlib import Path
from typing import Any, Generic, Iterable, Sequence, TypeVar
from unittest import IsolatedAsyncioTestCase, SkipTest

from sobiraka.models import Book, Page
from sobiraka.processing.abstract import Plainifier, Processor

T = TypeVar('T', bound=Processor)


class BookTestCase(IsolatedAsyncioTestCase, Generic[T]):
    maxDiff = None

    def load_book(self) -> Book:
        book_yaml = self.dir / 'book.yaml'
        return Book.from_manifest(book_yaml)

    async def asyncSetUp(self):
        await super().asyncSetUp()

        filepath = Path(getfile(self.__class__))
        self.dir: Path = filepath.parent

        self.book = self.load_book()

        awaitables = tuple(self.processor.process2(page) for page in self.book.pages)
        await gather(*awaitables)

    @cached_property
    def processor(self) -> T:
        return Plainifier(self.book)

    def subTest(self, msg: Any = ..., **params: Any):
        match msg:
            case Page() as page:
                if page.relative_path == Path('.'):
                    return super().subTest('')
                else:
                    return super().subTest(page.relative_path.with_suffix(''))
            case _:
                return super().subTest(msg)

    @staticmethod
    def assertNoDiff(expected: Sequence[str], actual: Sequence[str]):
        diff = list(unified_diff(expected, actual, n=1000))
        if diff:
            raise AssertionError('\n\n' + '\n'.join(diff[3:]))

    def for_each_expected(self, suffix: str, *, subdir: str = '') -> Iterable[tuple[Page, Path]]:
        ok = True
        for page in self.book.pages:
            expected = self.dir / 'expected' / subdir / page.relative_path.with_suffix(suffix)
            if expected.exists():
                yield page, expected
            else:
                ok = False
                with self.subTest(page):
                    raise SkipTest
        if not ok:
            raise SkipTest

    def test_errors(self):
        for page in self.book.pages:
            with self.subTest(page):
                self.assertEqual(set(), self.processor.errors[page])
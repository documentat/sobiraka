from functools import cached_property

from abstracttests.booktestcase import BookTestCase
from sobiraka.processing import Linter


class AbstractLintingTest(BookTestCase[Linter]):
    maxDiff = None

    @cached_property
    def processor(self) -> Linter:
        return Linter(self.book)

    async def test_misspelled_words(self):
        for page, expected in self.for_each_expected('.misspelled-words'):
            with self.subTest(page):
                expected = expected.read_text().splitlines()
                await self.processor.check()
                actual = self.processor.misspelled_words[page]
                self.assertNoDiff(expected, actual)

    async def test_phrases(self):
        for page, expected in self.for_each_expected('.phrases'):
            with self.subTest(page):
                expected = expected.read_text().splitlines()
                actual = []
                async for phrase in self.processor.phrases(page):
                    actual.append(phrase)
                self.assertNoDiff(expected, actual)


del BookTestCase
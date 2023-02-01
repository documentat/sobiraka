from functools import cached_property

from abstracttests.booktestcase import BookTestCase
from sobiraka.processing import SpellChecker


class AbstractLintingTest(BookTestCase[SpellChecker]):
    maxDiff = None

    @cached_property
    def processor(self) -> SpellChecker:
        return SpellChecker(self.book)

    async def test_misspelled_words(self):
        for page, expected in self.for_each_expected('.misspelled-words'):
            with self.subTest(page):
                expected = expected.read_text().splitlines()
                await self.processor.run()
                actual = self.processor.misspelled_words[page]
                self.assertNoDiff(expected, actual)

    async def test_phrases(self):
        for page, expected in self.for_each_expected('.phrases'):
            with self.subTest(page):
                expected = expected.read_text().splitlines()
                actual = await self.processor.phrases(page)
                self.assertNoDiff(expected, actual)


del BookTestCase
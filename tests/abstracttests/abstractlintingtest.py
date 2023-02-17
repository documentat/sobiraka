from functools import cached_property

from abstracttests.booktestcase import BookTestCase
from sobiraka.linter import Linter


class AbstractLintingTest(BookTestCase[Linter]):
    maxDiff = None

    @cached_property
    def processor(self) -> Linter:
        return Linter(self.book)

    async def test_issues(self):
        for page, expected in self.for_each_expected('.issues'):
            with self.subTest(page):
                expected = expected.read_text().splitlines()
                await self.processor.check()
                actual_issues = self.processor.issues[page]
                actual = list(map(str, actual_issues))
                self.assertNoDiff(expected, actual)

    async def test_phrases(self):
        for page, expected in self.for_each_expected('.phrases'):
            with self.subTest(page):
                expected = tuple(expected.read_text().splitlines())
                page_data = await self.processor.data(page)
                actual = tuple(x.text for x in page_data.phrases)
                self.assertNoDiff(expected, actual)


del BookTestCase
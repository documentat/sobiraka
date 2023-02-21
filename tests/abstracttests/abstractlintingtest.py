from abstracttests.booktestcase import BookTestCase
from sobiraka.linter import Linter


class AbstractLintingTest(BookTestCase[Linter]):
    maxDiff = None

    def _init_processor(self) -> Linter:
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
                tm = await self.processor.tm(page)
                actual = tuple(x.text for x in tm.phrases)
                self.assertNoDiff(expected, actual)


del BookTestCase
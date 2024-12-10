from helpers import assertNoDiff
from sobiraka.linter import Linter
from sobiraka.processing.txt import TextModel
from sobiraka.runtime import RT
from .projectdirtestcase import ProjectDirTestCase


class AbstractLintingTest(ProjectDirTestCase[Linter]):
    maxDiff = None

    def _init_processor(self) -> Linter:
        return Linter(self.project.volumes[0])

    async def test_issues(self):
        for page, expected in self.for_each_expected('.issues'):
            with self.subTest(page):
                expected = expected.read_text().splitlines()
                await self.processor.run()
                actual_issues = RT[page].issues
                actual = list(map(str, actual_issues))
                assertNoDiff(expected, actual)

    async def test_phrases(self):
        for page, expected in self.for_each_expected('.phrases'):
            with self.subTest(page):
                tm: TextModel = self.processor.tm[page]

                expected = tuple(expected.read_text().splitlines())
                actual = tuple(x.text for x in tm.phrases)

                assertNoDiff(expected, actual)


del ProjectDirTestCase

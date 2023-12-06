from abstracttests.abstracttestwithrttmp import AbstractTestWithRtTmp
from abstracttests.projectdirtestcase import ProjectDirTestCase
from helpers import assertNoDiff
from sobiraka.processing import HtmlBuilder
from sobiraka.runtime import RT


class HtmlProjectTestCase(ProjectDirTestCase[HtmlBuilder], AbstractTestWithRtTmp):

    def _init_processor(self):
        return HtmlBuilder(self.project, RT.TMP)

    async def test_html(self):
        await self.processor.run()

        for page, expected in self.for_each_expected('.html'):
            with self.subTest(page):
                expected = tuple(expected.read_text().splitlines())
                actual = self.processor.get_target_path(page).read_text().splitlines()
                assertNoDiff(expected, actual)


del ProjectDirTestCase, AbstractTestWithRtTmp

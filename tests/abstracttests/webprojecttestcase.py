from .abstracttestwithrt import AbstractTestWithRtTmp
from .projectdirtestcase import ProjectDirTestCase
from helpers import assertNoDiff
from sobiraka.processing import WebBuilder
from sobiraka.runtime import RT


class WebProjectTestCase(ProjectDirTestCase[WebBuilder], AbstractTestWithRtTmp):

    def _init_builder(self):
        return WebBuilder(self.project, RT.TMP)

    async def test_html(self):
        await self.builder.run()

        for page, expected in self.for_each_expected('.html'):
            with self.subTest(page):
                expected = tuple(expected.read_text().splitlines())
                actual = self.builder.get_target_path(page).read_text().splitlines()
                assertNoDiff(expected, actual)


del ProjectDirTestCase, AbstractTestWithRtTmp

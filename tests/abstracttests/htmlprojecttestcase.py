from pathlib import Path
from tempfile import TemporaryDirectory

from abstracttests.projectdirtestcase import ProjectDirTestCase
from sobiraka.processing import HtmlBuilder
from testutils import assertNoDiff


class HtmlProjectTestCase(ProjectDirTestCase[HtmlBuilder]):
    async def asyncSetUp(self):
        output_dir = self.enterContext(TemporaryDirectory(prefix='sobiraka-test-'))
        self.output_dir = Path(output_dir)

        await super().asyncSetUp()

    def _init_processor(self):
        return HtmlBuilder(self.project, self.output_dir)

    async def test_html(self):
        await self.processor.run()

        for page, expected in self.for_each_expected('.html'):
            with self.subTest(page):
                expected = tuple(expected.read_text().splitlines())
                actual = self.processor.get_target_path(page).read_text().splitlines()
                assertNoDiff(expected, actual)

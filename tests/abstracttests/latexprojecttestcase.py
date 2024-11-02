from helpers import assertNoDiff
from sobiraka.models import PageStatus
from sobiraka.processing import LatexBuilder
from sobiraka.runtime import RT
from .abstractvisualpdftestcase import AbstractVisualPdfTestCase


class LatexProjectTestCase(AbstractVisualPdfTestCase[LatexBuilder]):
    REQUIRE = PageStatus.PROCESS4

    def _init_builder(self):
        return LatexBuilder(self.project.volumes[0], RT.TMP / 'test.pdf')

    async def test_latex(self):
        for page, expected in self.for_each_expected('.tex', subdir='tex'):
            with self.subTest(page):
                expected = expected.read_text().splitlines()
                actual = RT[page].bytes.decode('utf-8').splitlines()
                assertNoDiff(expected, actual)


del AbstractVisualPdfTestCase

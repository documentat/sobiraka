import hashlib
from asyncio import create_subprocess_exec

from helpers import assertNoDiff
from sobiraka.models import PageStatus
from sobiraka.processing import LatexBuilder
from sobiraka.runtime import RT
from .abstracttestwithrt import AbstractTestWithRtTmp
from .projectdirtestcase import ProjectDirTestCase


class LatexProjectTestCase(ProjectDirTestCase[LatexBuilder], AbstractTestWithRtTmp):
    REQUIRE = PageStatus.PROCESS4

    def _init_processor(self):
        return LatexBuilder(self.project.volumes[0], RT.TMP / 'test.pdf')

    async def test_latex(self):
        for page, expected in self.for_each_expected('.tex', subdir='tex'):
            with self.subTest(page):
                expected = expected.read_text().splitlines()
                actual = RT[page].bytes.decode('utf-8').splitlines()
                assertNoDiff(expected, actual)

    async def test_pdf(self):
        await self.processor.run()

        pdftoppm = await create_subprocess_exec('pdftoppm', '-png', 'test.pdf', 'page', cwd=RT.TMP)
        await pdftoppm.wait()

        expected_dir = self.dir / 'expected' / 'pdf'
        expected_count = sum(1 for f in expected_dir.iterdir() if f.name.endswith('.png'))
        actual_count = sum(1 for f in RT.TMP.iterdir() if f.name.endswith('.png'))
        self.assertEqual(expected_count, actual_count)

        for p in range(1, expected_count + 1):
            with self.subTest(f'page-{p}'):
                with (expected_dir / f'page-{p}.png').open('rb') as file:
                    expected_sha = hashlib.file_digest(file, 'sha1')
                with (RT.TMP / f'page-{p}.png').open('rb') as file:
                    actual_sha = hashlib.file_digest(file, 'sha1')
                self.assertEqual(expected_sha.hexdigest(), actual_sha.hexdigest())


del ProjectDirTestCase, AbstractTestWithRtTmp

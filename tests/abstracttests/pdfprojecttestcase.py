import hashlib
from asyncio import create_subprocess_exec
from pathlib import Path
from tempfile import TemporaryDirectory

from sobiraka.processing import PdfBuilder
from .abstracttestwithrttmp import AbstractTestWithRtTmp
from .projecttestcase import ProjectTestCase


class PdfProjectTestCase(ProjectTestCase[PdfBuilder], AbstractTestWithRtTmp):
    async def asyncSetUp(self):
        output_dir = self.enterContext(TemporaryDirectory(prefix='sobiraka-test-'))
        self.output_dir = Path(output_dir)

        await super().asyncSetUp()

    def _init_processor(self):
        return PdfBuilder(self.project.volumes[0], self.output_dir / 'test.pdf')

    async def test_latex(self):
        for page, expected in self.for_each_expected('.tex', subdir='tex'):
            with self.subTest(page):
                expected = expected.read_text().splitlines()
                await self.processor.generate_latex_for_page(page)
                actual = self.processor._latex[page].decode('utf-8').splitlines()
                self.assertNoDiff(expected, actual)

    async def test_pdf(self):
        await self.processor.run()

        pdftoppm = await create_subprocess_exec('pdftoppm', '-png', 'test.pdf', 'page', cwd=self.output_dir)
        await pdftoppm.wait()

        expected_count = len(list((self.dir / 'expected' / 'pdf').glob('*.png')))
        actual_count = len(list(self.output_dir.glob('*.png')))
        self.assertEqual(expected_count, actual_count)

        for p in range(1, expected_count + 1):
            with self.subTest(f'page-{p}'):
                with (self.dir / 'expected' / 'pdf' / f'page-{p}.png').open('rb') as file:
                    expected_sha = hashlib.file_digest(file, 'sha1')
                with (self.output_dir / f'page-{p}.png').open('rb') as file:
                    actual_sha = hashlib.file_digest(file, 'sha1')
                self.assertEqual(expected_sha.hexdigest(), actual_sha.hexdigest())


del ProjectTestCase, AbstractTestWithRtTmp

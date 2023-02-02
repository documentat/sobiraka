import hashlib
from asyncio import create_subprocess_exec
from functools import cached_property
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import SkipTest

from sobiraka.processing import PdfBuilder
from .abstracttestwithrttmp import AbstractTestWithRtTmp
from .booktestcase import BookTestCase


class PdfBookTestCase(BookTestCase[PdfBuilder], AbstractTestWithRtTmp):
    @cached_property
    def processor(self):
        return PdfBuilder(self.book)

    async def test_latex(self):
        try:
            expected_latex = (self.dir / 'expected' / 'expected.tex').read_text()
        except FileNotFoundError:
            raise SkipTest

        with BytesIO() as latex_output:
            await self.processor.generate_latex(latex_output)
            latex_output.seek(0)
            latex = latex_output.read().decode('utf-8')

        self.assertEqual(expected_latex, latex)

    async def test_pdf(self):
        with TemporaryDirectory(prefix='sobiraka-test-') as temp_dir:
            temp_dir = Path(temp_dir)

            await self.processor.run(temp_dir / 'test.pdf')

            pdftoppm = await create_subprocess_exec('pdftoppm', '-png', 'test.pdf', 'page', cwd=temp_dir)
            await pdftoppm.wait()

            expected_count = len(list((self.dir / 'expected').glob('*.png')))
            actual_count = len(list(temp_dir.glob('*.png')))
            self.assertEqual(expected_count, actual_count)

            for p in range(1, expected_count + 1):
                with self.subTest(f'page-{p}'):
                    with (self.dir / 'expected' / f'page-{p}.png').open('rb') as file:
                        expected_sha = hashlib.file_digest(file, 'sha1')
                    with (temp_dir / f'page-{p}.png').open('rb') as file:
                        actual_sha = hashlib.file_digest(file, 'sha1')
                    self.assertEqual(expected_sha.hexdigest(), actual_sha.hexdigest())


del BookTestCase, AbstractTestWithRtTmp
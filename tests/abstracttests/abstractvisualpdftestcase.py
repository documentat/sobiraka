import hashlib
import inspect
import shutil
from asyncio import create_subprocess_exec
from typing import Generic, TypeVar

from sobiraka.models import PageStatus
from sobiraka.processing.abstract import Processor
from sobiraka.runtime import RT
from sobiraka.utils import AbsolutePath
from .abstracttestwithrt import AbstractTestWithRtTmp
from .projectdirtestcase import ProjectDirTestCase
from .projecttestcase import ProjectTestCase

T = TypeVar('T', bound=Processor)


class AbstractVisualPdfTestCase(ProjectTestCase, AbstractTestWithRtTmp, Generic[T]):
    REQUIRE = PageStatus.PROCESS4

    @classmethod
    def expected_dir(cls) -> AbsolutePath:
        this_file = AbsolutePath(inspect.getfile(cls))
        this_dir = this_file.parent
        if this_file.name == 'test.py':
            expected_dir = this_dir / 'expected' / 'pdf'
        else:
            expected_dir = this_dir / 'expected' / cls.__name__
        expected_dir.mkdir(parents=True, exist_ok=True)
        return expected_dir

    @classmethod
    def results_dir(cls) -> AbsolutePath:
        this_file = AbsolutePath(inspect.getfile(cls))
        this_dir = this_file.parent
        if this_file.name == 'test.py':
            results_dir = this_dir / 'actual' / 'pdf'
        else:
            results_dir = this_dir / 'actual' / cls.__name__
        results_dir.mkdir(parents=True, exist_ok=True)
        return results_dir

    async def test_pdf(self):
        expected_screenshots = self.expected_dir().iterdir()
        expected_screenshots = list(f for f in expected_screenshots if f.name.endswith('.png'))
        expected_screenshots.sort()

        # Generate PDF, then convert it to a series of PNG screenshots
        await self.processor.run()
        (RT.TMP / 'screenshots').mkdir()
        pdftoppm = await create_subprocess_exec('pdftoppm', '-png', 'test.pdf', 'screenshots/page', cwd=RT.TMP)
        await pdftoppm.wait()
        actual_screenshots: list[AbsolutePath] = list(sorted((RT.TMP / 'screenshots').iterdir()))

        potentially_outdated_test = False
        try:
            # Make sure the number of screenshots is as expected
            if len(expected_screenshots) != len(actual_screenshots):
                potentially_outdated_test = True
                self.fail('Page count is wrong!')

            # Compare each actual screenshot with its expected counterpart by their hash sums
            for p, (expected, actual) in enumerate(zip(expected_screenshots, actual_screenshots)):
                with self.subTest(expected.stem):
                    self.assertEqual(f'page-{p + 1}.png', expected.name)
                    self.assertEqual(f'page-{p + 1}.png', actual.name)
                    with expected.open('rb') as file:
                        expected_sha = hashlib.file_digest(file, 'sha1')
                    with actual.open('rb') as file:
                        actual_sha = hashlib.file_digest(file, 'sha1')

                    if expected_sha.hexdigest() != actual_sha.hexdigest():
                        potentially_outdated_test = True
                        self.fail('The screenshot checksum test failed.')

        finally:
            # If something goes wrong, copy the new files to the test directory for a manual investigation
            if potentially_outdated_test:
                shutil.copytree(RT.TMP / 'screenshots', self.results_dir(), dirs_exist_ok=True)


del ProjectDirTestCase, AbstractTestWithRtTmp
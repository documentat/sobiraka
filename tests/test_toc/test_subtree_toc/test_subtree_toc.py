from pathlib import Path
from unittest import main
from unittest.mock import Mock

from abstracttests.projecttestcase import ProjectTestCase
from helpers import assertNoDiff
from sobiraka.models import FileSystem, Project, SubtreeToc, Volume
from sobiraka.processing.abstract import ProjectProcessor
from test_toc.datasets import dataset_paths


class AbstractTestSubtreeToc(ProjectTestCase):
    ext: str

    def _init_project(self) -> Project:
        fs = Mock(FileSystem)
        return Project(fs, {
            Path('src'): Volume(dataset_paths(self.ext)),
        })

    def _init_processor(self):
        return ProjectProcessor(self.project)

    async def test_subtree_toc(self):
        for page, expected in self.for_each_expected(f'.{self.ext}', subdir=self.ext):
            with self.subTest(page):
                expected = expected.read_text('utf-8')
                actual = await SubtreeToc(self.processor, page)()
                assertNoDiff(expected.splitlines(), actual.splitlines())


class TestSubtreeToc_MD(AbstractTestSubtreeToc):
    ext = 'md'


class TestSubtreeToc_RST(AbstractTestSubtreeToc):
    ext = 'rst'


del ProjectTestCase, AbstractTestSubtreeToc

if __name__ == '__main__':
    main()

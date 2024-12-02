from math import inf

from abstracttests.projecttestcase import ProjectTestCase
from helpers import FakeBuilder, FakeFileSystem
from sobiraka.models import Page, PageStatus, Project, Volume
from sobiraka.models.config import CombinedToc, Config, Config_Content
from sobiraka.processing.toc import Toc, TocItem, toc
from sobiraka.utils import RelativePath, TocNumber


class TestNumerateRoot(ProjectTestCase[FakeBuilder]):
    REQUIRE = PageStatus.PROCESS3

    def _init_project(self) -> Project:
        config = Config(
            content=Config_Content(numeration=True),
        )
        return Project(FakeFileSystem(), {
            RelativePath('src'): Volume(config, {
                RelativePath(): Page('# Root \n## Section 1\n## Section 2'),
                RelativePath('section-3.md'): Page('# Section 3'),
                RelativePath('section-4.md'): Page('# Section 4'),
            }),
        })

    async def test_numerate(self):
        expected = Toc(
            TocItem('Section 1', '#section-1', number=TocNumber(1)),
            TocItem('Section 2', '#section-2', number=TocNumber(2)),
            TocItem('Section 3', 'section-3.md', number=TocNumber(3)),
            TocItem('Section 4', 'section-4.md', number=TocNumber(4)),
        )

        root_page = self.project.get_volume().root_page
        actual = toc(root_page,
                     builder=self.builder,
                     toc_depth=inf,
                     combined_toc=CombinedToc.ALWAYS,
                     current_page=root_page)

        self.assertEqual(expected, actual)

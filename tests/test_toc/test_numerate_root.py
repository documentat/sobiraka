from math import inf

from abstracttests.projecttestcase import ProjectTestCase
from helpers import FakeBuilder
from helpers.fakeproject import FakeProject, FakeVolume
from sobiraka.models import Project, Status
from sobiraka.models.config import CombinedToc, Config, Config_Content, Config_Paths
from sobiraka.processing.toc import Toc, TocItem, toc
from sobiraka.utils import RelativePath, TocNumber


class TestNumerateRoot(ProjectTestCase[FakeBuilder]):
    REQUIRE = Status.PROCESS3

    def _init_project(self) -> Project:
        config = Config(
            paths=Config_Paths(root=RelativePath('src')),
            content=Config_Content(numeration=True),
        )
        return FakeProject({
            'src': FakeVolume(config, {
                'index.md': '# Root \n## Section 1\n## Section 2',
                'section-3.md': '# Section 3',
                'section-4.md': '# Section 4',
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

from math import inf
from unittest import main
from unittest.mock import Mock

from abstracttests.projecttestcase import ProjectTestCase
from helpers import FakeBuilder
from sobiraka.models import FileSystem, Page, Project, Volume
from sobiraka.models.config import CombinedToc
from sobiraka.processing.toc import Toc, TocItem, toc
from sobiraka.utils import RelativePath


class AbstractTestTocCombine(ProjectTestCase[FakeBuilder]):
    combine: CombinedToc
    toc_depth: int | float = inf
    expected: Toc

    def _init_project(self) -> Project:
        return Project(Mock(FileSystem), {
            RelativePath('src'): Volume({
                RelativePath('section1'): Page('# Section 1\n## Paragraph 1'),
                RelativePath('section1/page1.md'): Page('# Page 1.1\n## Paragraph 1\n### Subparagraph'),  # <- current
                RelativePath('section1/page2.md'): Page('# Page 1.2\n## Paragraph 1'),
                RelativePath('section2'): Page('# Section 2\n## Paragraph 1'),
                RelativePath('section2/page1.md'): Page('# Page 2.1\n## Paragraph 1'),
                RelativePath('section2/page2.md'): Page('# Page 2.2\n## Paragraph 1'),
            })
        })

    def test_toc_combine(self):
        self.maxDiff = None

        volume = self.project.get_volume()
        actual = toc(volume.root_page,
                     builder=self.builder,
                     toc_depth=self.toc_depth,
                     combined_toc=self.combine,
                     current_page=volume.pages_by_path[RelativePath('section1/page1.md')])
        self.assertEqual(str(self.expected), str(actual))


class TestTocCombine_Never(AbstractTestTocCombine):
    combine = CombinedToc.NEVER
    expected = Toc(
        TocItem('Section 1', '.', is_breadcrumb=True, children=Toc(
            TocItem('Page 1.1', '', is_current=True, is_breadcrumb=True),
            TocItem('Page 1.2', 'page2.md'),
        )),
        TocItem('Section 2', '../section2', children=Toc(
            TocItem('Page 2.1', '../section2/page1.md'),
            TocItem('Page 2.2', '../section2/page2.md'),
        )),
    )


class TestTocCombine_Always(AbstractTestTocCombine):
    combine = CombinedToc.ALWAYS
    expected = Toc(
        TocItem('Section 1', '.', is_breadcrumb=True, children=Toc(
            TocItem('Paragraph 1', '.#paragraph-1'),
            TocItem('Page 1.1', '', is_current=True, is_breadcrumb=True, children=Toc(
                TocItem('Paragraph 1', '#paragraph-1', children=Toc(
                    TocItem('Subparagraph', '#subparagraph'),
                )),
            )),
            TocItem('Page 1.2', 'page2.md', children=Toc(
                TocItem('Paragraph 1', 'page2.md#paragraph-1'),
            )),
        )),
        TocItem('Section 2', '../section2', children=Toc(
            TocItem('Paragraph 1', '../section2#paragraph-1'),
            TocItem('Page 2.1', '../section2/page1.md', children=Toc(
                TocItem('Paragraph 1', '../section2/page1.md#paragraph-1'),
            )),
            TocItem('Page 2.2', '../section2/page2.md', children=Toc(
                TocItem('Paragraph 1', '../section2/page2.md#paragraph-1'),
            )),
        )),
    )


class TestTocCombine_Current(AbstractTestTocCombine):
    combine = CombinedToc.CURRENT
    expected = Toc(
        TocItem('Section 1', '.', is_breadcrumb=True, children=Toc(
            TocItem('Page 1.1', '', is_current=True, is_breadcrumb=True, children=Toc(
                TocItem('Paragraph 1', '#paragraph-1', children=Toc(
                    TocItem('Subparagraph', '#subparagraph'),
                )),
            )),
            TocItem('Page 1.2', 'page2.md'),
        )),
        TocItem('Section 2', '../section2', children=Toc(
            TocItem('Page 2.1', '../section2/page1.md'),
            TocItem('Page 2.2', '../section2/page2.md'),
        )),
    )


class TestTocCombine_Current_LimitDepth_4(TestTocCombine_Current):
    toc_depth = 4


class TestTocCombine_Current_LimitDepth_3(TestTocCombine_Current):
    toc_depth = 3
    expected = Toc(
        TocItem('Section 1', '.', is_breadcrumb=True, children=Toc(
            TocItem('Page 1.1', '', is_current=True, is_breadcrumb=True, children=Toc(
                TocItem('Paragraph 1', '#paragraph-1'),
            )),
            TocItem('Page 1.2', 'page2.md'),
        )),
        TocItem('Section 2', '../section2', children=Toc(
            TocItem('Page 2.1', '../section2/page1.md'),
            TocItem('Page 2.2', '../section2/page2.md'),
        )),
    )


class TestTocCombine_Current_LimitDepth_2(TestTocCombine_Current):
    toc_depth = 2
    expected = Toc(
        TocItem('Section 1', '.', is_breadcrumb=True, children=Toc(
            TocItem('Page 1.1', '', is_current=True, is_breadcrumb=True),
            TocItem('Page 1.2', 'page2.md'),
        )),
        TocItem('Section 2', '../section2', children=Toc(
            TocItem('Page 2.1', '../section2/page1.md'),
            TocItem('Page 2.2', '../section2/page2.md'),
        )),
    )


class TestTocCombine_Current_LimitDepth_1(TestTocCombine_Current):
    toc_depth = 1
    expected = Toc(
        TocItem('Section 1', '.', is_breadcrumb=True, children=Toc(
            TocItem('Page 1.1', '', is_current=True, is_breadcrumb=True),
            TocItem('Page 1.2', 'page2.md'),
        )),
        TocItem('Section 2', '../section2'),
    )


del ProjectTestCase, AbstractTestTocCombine

if __name__ == '__main__':
    main()

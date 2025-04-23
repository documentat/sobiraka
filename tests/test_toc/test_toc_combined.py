from math import inf
from unittest import main

from abstracttests.projecttestcase import ProjectTestCase
from helpers import FakeBuilder
from helpers.fakeproject import FakeProject, FakeVolume
from sobiraka.models import Project
from sobiraka.models.config import CombinedToc
from sobiraka.processing.toc import Toc, TocItem, toc


class AbstractTestTocCombined(ProjectTestCase[FakeBuilder]):
    combined: CombinedToc
    toc_depth: int | float = inf
    expected: Toc

    def _init_project(self) -> Project:
        return FakeProject({
            'src': FakeVolume({
                'section1': {
                    'index.md': '# Section 1\n## Paragraph 1',
                    'page1.md': '# Page 1.1\n## Paragraph 1\n### Subparagraph',  # <- current page
                    'page2.md': '# Page 1.2\n## Paragraph 1',
                },
                'section2': {
                    'index.md': '# Section 2\n## Paragraph 1',
                    'page1.md': '# Page 2.1\n## Paragraph 1',
                    'page2.md': '# Page 2.2\n## Paragraph 1',
                },
            })
        })

    def test_toc_combined(self):
        self.maxDiff = None

        volume = self.project.get_volume()
        actual = toc(volume.root_page,
                     builder=self.builder,
                     toc_depth=self.toc_depth,
                     combined_toc=self.combined,
                     current_page=volume.get_page_by_location('/section1/page1'))
        self.assertEqual(str(self.expected), str(actual))


class TestTocCombine_Never(AbstractTestTocCombined):
    combined = CombinedToc.NEVER
    expected = Toc(
        TocItem('Section 1', './', is_breadcrumb=True, children=Toc(
            TocItem('Page 1.1', '', is_current=True, is_breadcrumb=True),
            TocItem('Page 1.2', 'page2.md'),
        )),
        TocItem('Section 2', '../section2/', children=Toc(
            TocItem('Page 2.1', '../section2/page1.md'),
            TocItem('Page 2.2', '../section2/page2.md'),
        )),
    )


class TestTocCombine_Always(AbstractTestTocCombined):
    combined = CombinedToc.ALWAYS
    expected = Toc(
        TocItem('Section 1', './', is_breadcrumb=True, children=Toc(
            TocItem('Paragraph 1', './#paragraph-1'),
            TocItem('Page 1.1', '', is_current=True, is_breadcrumb=True, children=Toc(
                TocItem('Paragraph 1', '#paragraph-1', children=Toc(
                    TocItem('Subparagraph', '#subparagraph'),
                )),
            )),
            TocItem('Page 1.2', 'page2.md', children=Toc(
                TocItem('Paragraph 1', 'page2.md#paragraph-1'),
            )),
        )),
        TocItem('Section 2', '../section2/', children=Toc(
            TocItem('Paragraph 1', '../section2/#paragraph-1'),
            TocItem('Page 2.1', '../section2/page1.md', children=Toc(
                TocItem('Paragraph 1', '../section2/page1.md#paragraph-1'),
            )),
            TocItem('Page 2.2', '../section2/page2.md', children=Toc(
                TocItem('Paragraph 1', '../section2/page2.md#paragraph-1'),
            )),
        )),
    )


class TestTocCombine_Current(AbstractTestTocCombined):
    combined = CombinedToc.CURRENT
    expected = Toc(
        TocItem('Section 1', './', is_breadcrumb=True, children=Toc(
            TocItem('Page 1.1', '', is_current=True, is_breadcrumb=True, children=Toc(
                TocItem('Paragraph 1', '#paragraph-1', children=Toc(
                    TocItem('Subparagraph', '#subparagraph'),
                )),
            )),
            TocItem('Page 1.2', 'page2.md'),
        )),
        TocItem('Section 2', '../section2/', children=Toc(
            TocItem('Page 2.1', '../section2/page1.md'),
            TocItem('Page 2.2', '../section2/page2.md'),
        )),
    )


class TestTocCombine_Current_LimitDepth_4(TestTocCombine_Current):
    toc_depth = 4


class TestTocCombine_Current_LimitDepth_3(TestTocCombine_Current):
    toc_depth = 3
    expected = Toc(
        TocItem('Section 1', './', is_breadcrumb=True, children=Toc(
            TocItem('Page 1.1', '', is_current=True, is_breadcrumb=True, children=Toc(
                TocItem('Paragraph 1', '#paragraph-1'),
            )),
            TocItem('Page 1.2', 'page2.md'),
        )),
        TocItem('Section 2', '../section2/', children=Toc(
            TocItem('Page 2.1', '../section2/page1.md'),
            TocItem('Page 2.2', '../section2/page2.md'),
        )),
    )


class TestTocCombine_Current_LimitDepth_2(TestTocCombine_Current):
    toc_depth = 2
    expected = Toc(
        TocItem('Section 1', './', is_breadcrumb=True, children=Toc(
            TocItem('Page 1.1', '', is_current=True, is_breadcrumb=True),
            TocItem('Page 1.2', 'page2.md'),
        )),
        TocItem('Section 2', '../section2/', children=Toc(
            TocItem('Page 2.1', '../section2/page1.md'),
            TocItem('Page 2.2', '../section2/page2.md'),
        )),
    )


class TestTocCombine_Current_LimitDepth_1(TestTocCombine_Current):
    toc_depth = 1
    expected = Toc(
        TocItem('Section 1', './', is_breadcrumb=True, children=Toc(
            TocItem('Page 1.1', '', is_current=True, is_breadcrumb=True),
            TocItem('Page 1.2', 'page2.md'),
        )),
        TocItem('Section 2', '../section2/'),
    )


del ProjectTestCase, AbstractTestTocCombined

if __name__ == '__main__':
    main()

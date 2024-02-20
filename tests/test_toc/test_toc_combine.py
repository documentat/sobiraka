from math import inf
from pathlib import Path
from unittest import main
from unittest.mock import Mock

from abstracttests.projecttestcase import ProjectTestCase
from helpers.fakeprocessor import FakeProcessor
from sobiraka.models import FileSystem, Page, Project, Volume
from sobiraka.models.config import CombinedToc
from sobiraka.processing.toc import Toc, TocItem, toc


class AbstractTestTocCombine(ProjectTestCase[FakeProcessor]):
    combine: CombinedToc
    expected: Toc

    def _init_project(self) -> Project:
        return Project(Mock(FileSystem), {
            Path('src'): Volume({
                Path('section1'): Page('# Section 1\n## Paragraph 1'),
                Path('section1/page1.md'): Page('# Page 1.1\n## Paragraph 1'),  # <- current page
                Path('section1/page2.md'): Page('# Page 1.2\n## Paragraph 1'),
                Path('section2'): Page('# Section 2\n## Paragraph 1'),
                Path('section2/page1.md'): Page('# Page 2.1\n## Paragraph 1'),
                Path('section2/page2.md'): Page('# Page 2.2\n## Paragraph 1'),
            })
        })

    def _init_processor(self):
        return FakeProcessor()

    def test_toc_combine(self):
        self.maxDiff = None

        volume = self.project.get_volume()
        actual = toc(volume,
                     processor=self.processor,
                     toc_depth=inf,
                     combined_toc=self.combine,
                     current_page=volume.pages_by_path[Path('section1/page1.md')])
        self.assertEqual(str(self.expected), str(actual))


class TestTocCombine_Never(AbstractTestTocCombine):
    combine = CombinedToc.NEVER
    expected = Toc(
        TocItem('Section 1', '.', is_selected=True, children=Toc(
            TocItem('Page 1.1', '', is_current=True, is_selected=True),
            TocItem('Page 1.2', 'page2.md'),
        )),
        TocItem('Section 2', '../section2', children=Toc(
            TocItem('Page 2.1', '../section2/page1.md'),
            TocItem('Page 2.2', '../section2/page2.md'),
        )),
    )


class TestTocCombine_Current(AbstractTestTocCombine):
    combine = CombinedToc.CURRENT
    expected = Toc(
        TocItem('Section 1', '.', is_selected=True, children=Toc(
            TocItem('Page 1.1', '', is_current=True, is_selected=True, children=Toc(
                TocItem('Paragraph 1', '#paragraph-1'),
            )),
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
        TocItem('Section 1', '.', is_selected=True, children=Toc(
            TocItem('Paragraph 1', '.#paragraph-1'),
            TocItem('Page 1.1', '', is_current=True, is_selected=True, children=Toc(
                TocItem('Paragraph 1', '#paragraph-1'),
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


del ProjectTestCase, AbstractTestTocCombine

if __name__ == '__main__':
    main()

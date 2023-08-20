import inspect
import re
from abc import ABCMeta
from pathlib import Path
from unittest import main
from unittest.mock import Mock

from bs4 import BeautifulSoup
from bs4.formatter import Formatter

from abstracttests.abstracttestwithrttmp import AbstractTestWithRtTmp
from abstracttests.projecttestcase import ProjectTestCase
from sobiraka.models import FileSystem, IndexPage, Page, Project, SubtreeToc, TocTreeItem, Volume
from sobiraka.processing import HtmlBuilder
from sobiraka.processing.abstract import ProjectProcessor
from sobiraka.processing.htmlbuilder import GlobalToc_HTML
from sobiraka.runtime import RT
from testutils import assertNoDiff


class TestToc(ProjectTestCase, metaclass=ABCMeta):
    ext: str

    def _init_project(self) -> Project:
        fs = Mock(FileSystem)
        return Project(fs, {
            Path('src'): Volume({
                Path() / f'0-index.{self.ext}': IndexPage('# ('),
                Path() / 'part1' / f'0-index.{self.ext}': IndexPage('# part1'),
                Path() / 'part1' / 'chapter1' / f'0-index.{self.ext}': IndexPage('# chapter1'),
                Path() / 'part1' / 'chapter1' / 'section1' / f'0-index.{self.ext}': IndexPage('# section1'),
                Path() / 'part1' / 'chapter1' / 'section1' / f'article1.{self.ext}': Page('# article1'),
                Path() / 'part1' / 'chapter1' / 'section1' / f'article2.{self.ext}': Page('# article2'),
                Path() / 'part1' / 'chapter1' / 'section2' / f'0-index.{self.ext}': IndexPage('# section2'),
                Path() / 'part1' / 'chapter1' / 'section2' / f'article1.{self.ext}': Page('# article1'),
                Path() / 'part1' / 'chapter1' / 'section2' / f'article2.{self.ext}': Page('# article2'),
                Path() / 'part1' / 'chapter2' / f'0-index.{self.ext}': IndexPage('# chapter2'),
                Path() / 'part1' / 'chapter2' / 'section1' / f'0-index.{self.ext}': IndexPage('# section1'),
                Path() / 'part1' / 'chapter2' / 'section1' / f'article1.{self.ext}': Page('# article1'),
                Path() / 'part1' / 'chapter2' / 'section1' / f'article2.{self.ext}': Page('# article2'),
                Path() / 'part1' / 'chapter2' / 'section2' / f'0-index.{self.ext}': IndexPage('# section2'),
                Path() / 'part1' / 'chapter2' / 'section2' / f'article1.{self.ext}': Page('# article1'),
                Path() / 'part1' / 'chapter2' / 'section2' / f'article2.{self.ext}': Page('# article2'),
                Path() / 'part2' / f'0-index.{self.ext}': IndexPage('# part2'),
                Path() / 'part2' / 'chapter1' / f'0-index.{self.ext}': IndexPage('# chapter1'),
                Path() / 'part2' / 'chapter1' / 'section1' / f'0-index.{self.ext}': IndexPage('# section1'),
                Path() / 'part2' / 'chapter1' / 'section1' / f'article1.{self.ext}': Page('# article1'),
                Path() / 'part2' / 'chapter1' / 'section1' / f'article2.{self.ext}': Page('# article2'),
                Path() / 'part2' / 'chapter1' / 'section2' / f'0-index.{self.ext}': IndexPage('# section2'),
                Path() / 'part2' / 'chapter1' / 'section2' / f'article1.{self.ext}': Page('# article1'),
                Path() / 'part2' / 'chapter1' / 'section2' / f'article2.{self.ext}': Page('# article2'),
                Path() / 'part2' / 'chapter2' / f'0-index.{self.ext}': IndexPage('# chapter2'),
                Path() / 'part2' / 'chapter2' / 'section1' / f'0-index.{self.ext}': IndexPage('# section1'),
                Path() / 'part2' / 'chapter2' / 'section1' / f'article1.{self.ext}': Page('# article1'),
                Path() / 'part2' / 'chapter2' / 'section1' / f'article2.{self.ext}': Page('# article2'),
                Path() / 'part2' / 'chapter2' / 'section2' / f'0-index.{self.ext}': IndexPage('# section2'),
                Path() / 'part2' / 'chapter2' / 'section2' / f'article1.{self.ext}': Page('# article1'),
                Path() / 'part2' / 'chapter2' / 'section2' / f'article2.{self.ext}': Page('# article2'),
            }),
        })

    def _init_processor(self):
        return ProjectProcessor(self.project)


class TestSubtreeToc(TestToc):
    async def test_subtree_toc(self):
        for page, expected in self.for_each_expected(f'.{self.ext}', subdir=f'subtree-{self.ext}'):
            with self.subTest(page):
                expected = expected.read_text('utf-8')
                actual = await SubtreeToc(self.processor, page)()
                assertNoDiff(expected.splitlines(), actual.splitlines())


class TestSubtreeToc_MD(TestSubtreeToc):
    ext = 'md'


class TestSubtreeToc_RST(TestSubtreeToc):
    ext = 'rst'


class TestGlobalToc(TestToc, AbstractTestWithRtTmp):
    ext = 'md'

    def _init_processor(self):
        return HtmlBuilder(self.project, RT.TMP)

    async def test_get_roots(self):
        expected: tuple[Page, ...] = (self.project.pages_by_path[Path('src/0-index.md')],)
        toc = GlobalToc_HTML(self.processor, self.project.get_volume(), NotImplemented)
        actual = toc.get_roots()
        self.assertSequenceEqual(expected, actual)

    async def test_global_toc_items(self):
        expected = [
            TocTreeItem('part1', 'part1/index.html', children=[
                TocTreeItem('chapter1', 'part1/chapter1/index.html', children=[
                    TocTreeItem('section1', 'part1/chapter1/section1/index.html', children=[
                        TocTreeItem('article1', 'part1/chapter1/section1/article1.html'),
                        TocTreeItem('article2', 'part1/chapter1/section1/article2.html'),
                    ]),
                    TocTreeItem('section2', 'part1/chapter1/section2/index.html', children=[
                        TocTreeItem('article1', 'part1/chapter1/section2/article1.html'),
                        TocTreeItem('article2', 'part1/chapter1/section2/article2.html'),
                    ]),
                ]),
                TocTreeItem('chapter2', 'part1/chapter2/index.html', children=[
                    TocTreeItem('section1', 'part1/chapter2/section1/index.html', children=[
                        TocTreeItem('article1', 'part1/chapter2/section1/article1.html'),
                        TocTreeItem('article2', 'part1/chapter2/section1/article2.html'),
                    ]),
                    TocTreeItem('section2', 'part1/chapter2/section2/index.html', children=[
                        TocTreeItem('article1', 'part1/chapter2/section2/article1.html'),
                        TocTreeItem('article2', 'part1/chapter2/section2/article2.html'),
                    ]),
                ]),
            ]),
            TocTreeItem('part2', 'part2/index.html', children=[
                TocTreeItem('chapter1', 'part2/chapter1/index.html', children=[
                    TocTreeItem('section1', 'part2/chapter1/section1/index.html', children=[
                        TocTreeItem('article1', 'part2/chapter1/section1/article1.html'),
                        TocTreeItem('article2', 'part2/chapter1/section1/article2.html'),
                    ]),
                    TocTreeItem('section2', 'part2/chapter1/section2/index.html', children=[
                        TocTreeItem('article1', 'part2/chapter1/section2/article1.html'),
                        TocTreeItem('article2', 'part2/chapter1/section2/article2.html'),
                    ]),
                ]),
                TocTreeItem('chapter2', 'part2/chapter2/index.html', children=[
                    TocTreeItem('section1', 'part2/chapter2/section1/index.html', children=[
                        TocTreeItem('article1', 'part2/chapter2/section1/article1.html'),
                        TocTreeItem('article2', 'part2/chapter2/section1/article2.html'),
                    ]),
                    TocTreeItem('section2', 'part2/chapter2/section2/index.html', children=[
                        TocTreeItem('article1', 'part2/chapter2/section2/article1.html'),
                        TocTreeItem('article2', 'part2/chapter2/section2/article2.html'),
                    ]),
                ]),
            ]),
        ]
        toc = GlobalToc_HTML(self.processor, self.project.get_volume(), self.project.pages[0])
        actual = await toc.items()
        self.assertEqual(expected, actual)

    async def test_global_toc_rendered(self):
        test_dir = Path(inspect.getfile(self.__class__)).parent

        for name, path in (('root', Path('0-index.md')),
                           ('nonroot', Path('part1/chapter1/section1/article1.md'))):
            page = self.project.get_volume().pages_by_path[path]
            with self.subTest(page):
                expected_file = test_dir / 'expected' / 'global-html' / f'from-{name}.html'

                expected = expected_file.read_text('utf-8')
                expected = BeautifulSoup(expected, 'html.parser').prettify(
                    formatter=Formatter(Formatter.HTML, indent=2))
                expected = re.sub(r'<(a|strong)([^>]*)>\n\s+([^>]+)\n\s+</\1>', r'<\1\2>\3</\1>', expected)

                actual = await GlobalToc_HTML(self.processor, page.volume, page)()
                actual = BeautifulSoup(actual, 'html.parser').prettify(formatter=Formatter(Formatter.HTML, indent=2))
                actual = re.sub(r'<(a|strong)([^>]*)>\n\s+([^>]+)\n\s+</\1>', r'<\1\2>\3</\1>', actual)

                assertNoDiff(expected.splitlines(), actual.splitlines())


del ProjectTestCase, TestToc, TestSubtreeToc

if __name__ == '__main__':
    main()

import re
from math import inf
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import main
from unittest.mock import Mock

from abstracttests.projecttestcase import ProjectTestCase
from bs4 import BeautifulSoup
from bs4.formatter import Formatter
from helpers import assertNoDiff
from sobiraka.models import FileSystem, IndexPage, Page, Project, Volume
from sobiraka.models.config import Config, Config_HTML
from sobiraka.processing import HtmlBuilder
from sobiraka.processing.toc import Toc, TocItem, toc


class AbstractTestCrossPageToc(ProjectTestCase):
    toc_expansion: int | float

    async def asyncSetUp(self):
        self.output = Path(self.enterContext(TemporaryDirectory(prefix='sobiraka-test-')))
        await super().asyncSetUp()

    def _init_project(self) -> Project:
        fs = Mock(FileSystem)
        config = Config(html=Config_HTML(toc_expansion=self.toc_expansion))
        return Project(fs, {
            Path('src'): Volume(config, dataset_paths('md')),
        })

    def _init_processor(self):
        return HtmlBuilder(self.project, self.output)

    async def test_subtree_toc(self):
        data = {
            Path('0-index.md'): expected_paths_from_root(self.toc_expansion),
            Path('part1/0-index.md'): expected_paths_from_p1(self.toc_expansion),
            Path('part1/chapter1/0-index.md'): expected_paths_from_p1c1(self.toc_expansion),
            Path('part1/chapter1/section1/0-index.md'): expected_paths_from_p1c1s1(self.toc_expansion),
            Path('part1/chapter1/section1/article1.md'): expected_paths_from_p1c1s1a1(self.toc_expansion),
        }
        for path, expected in data.items():
            page = self.project.get_volume().pages_by_path[path]
            with self.subTest(page):
                actual = toc(page,
                             processor=self.processor,
                             current_page=page,
                             toc_expansion=self.toc_expansion)
                self.assertEqual(expected, actual)

    async def test_global_toc_rendered(self):
        data = {
            Path('0-index.md'): 'from-root.html',
            Path('part1/chapter1/section1/article1.md'): 'from-nonroot.html',
        }
        for path, name in data.items():
            page = self.project.get_volume().pages_by_path[path]
            with self.subTest(page):
                expected_file = Path(__file__).parent / 'expected' / str(self.toc_expansion) / name

                expected = expected_file.read_text('utf-8')
                expected = BeautifulSoup(expected, 'html.parser').prettify(
                    formatter=Formatter(Formatter.HTML, indent=2))
                expected = re.sub(r'<(a|strong)([^>]*)>\n\s+([^>]+)\n\s+</\1>', r'<\1\2>\3</\1>', expected)

                actual = Toc(toc(self.project.get_volume(),
                                 processor=self.processor,
                                 current_page=page,
                                 toc_expansion=self.toc_expansion))
                actual = str(actual)
                actual = BeautifulSoup(actual, 'html.parser').prettify(formatter=Formatter(Formatter.HTML, indent=2))
                actual = re.sub(r'<(a|strong)([^>]*)>\n\s+([^>]+)\n\s+</\1>', r'<\1\2>\3</\1>', actual)

                assertNoDiff(expected.splitlines(), actual.splitlines())


class TestCrossPageToc_1(AbstractTestCrossPageToc):
    toc_expansion = 1


class TestCrossPageToc_2(AbstractTestCrossPageToc):
    toc_expansion = 2


class TestCrossPageToc_3(AbstractTestCrossPageToc):
    toc_expansion = 3


class TestCrossPageToc_Infinity(AbstractTestCrossPageToc):
    toc_expansion = inf


del ProjectTestCase, AbstractTestCrossPageToc


################################################################################

def dataset_paths(ext: str) -> dict[Path, Page]:
    return {
        Path() / f'0-index.{ext}': IndexPage('# root'),
        Path() / 'part1' / f'0-index.{ext}': IndexPage('# part1'),
        Path() / 'part1' / 'chapter1' / f'0-index.{ext}': IndexPage('# chapter1'),
        Path() / 'part1' / 'chapter1' / 'section1' / f'0-index.{ext}': IndexPage('# section1'),
        Path() / 'part1' / 'chapter1' / 'section1' / f'article1.{ext}': Page('# article1'),
        Path() / 'part1' / 'chapter1' / 'section1' / f'article2.{ext}': Page('# article2'),
        Path() / 'part1' / 'chapter1' / 'section2' / f'0-index.{ext}': IndexPage('# section2'),
        Path() / 'part1' / 'chapter1' / 'section2' / f'article1.{ext}': Page('# article1'),
        Path() / 'part1' / 'chapter1' / 'section2' / f'article2.{ext}': Page('# article2'),
        Path() / 'part1' / 'chapter2' / f'0-index.{ext}': IndexPage('# chapter2'),
        Path() / 'part1' / 'chapter2' / 'section1' / f'0-index.{ext}': IndexPage('# section1'),
        Path() / 'part1' / 'chapter2' / 'section1' / f'article1.{ext}': Page('# article1'),
        Path() / 'part1' / 'chapter2' / 'section1' / f'article2.{ext}': Page('# article2'),
        Path() / 'part1' / 'chapter2' / 'section2' / f'0-index.{ext}': IndexPage('# section2'),
        Path() / 'part1' / 'chapter2' / 'section2' / f'article1.{ext}': Page('# article1'),
        Path() / 'part1' / 'chapter2' / 'section2' / f'article2.{ext}': Page('# article2'),
        Path() / 'part2' / f'0-index.{ext}': IndexPage('# part2'),
        Path() / 'part2' / 'chapter1' / f'0-index.{ext}': IndexPage('# chapter1'),
        Path() / 'part2' / 'chapter1' / 'section1' / f'0-index.{ext}': IndexPage('# section1'),
        Path() / 'part2' / 'chapter1' / 'section1' / f'article1.{ext}': Page('# article1'),
        Path() / 'part2' / 'chapter1' / 'section1' / f'article2.{ext}': Page('# article2'),
        Path() / 'part2' / 'chapter1' / 'section2' / f'0-index.{ext}': IndexPage('# section2'),
        Path() / 'part2' / 'chapter1' / 'section2' / f'article1.{ext}': Page('# article1'),
        Path() / 'part2' / 'chapter1' / 'section2' / f'article2.{ext}': Page('# article2'),
        Path() / 'part2' / 'chapter2' / f'0-index.{ext}': IndexPage('# chapter2'),
        Path() / 'part2' / 'chapter2' / 'section1' / f'0-index.{ext}': IndexPage('# section1'),
        Path() / 'part2' / 'chapter2' / 'section1' / f'article1.{ext}': Page('# article1'),
        Path() / 'part2' / 'chapter2' / 'section1' / f'article2.{ext}': Page('# article2'),
        Path() / 'part2' / 'chapter2' / 'section2' / f'0-index.{ext}': IndexPage('# section2'),
        Path() / 'part2' / 'chapter2' / 'section2' / f'article1.{ext}': Page('# article1'),
        Path() / 'part2' / 'chapter2' / 'section2' / f'article2.{ext}': Page('# article2'),
    }


def expected_paths_from_root(toc_expansion: int | float) -> Toc:
    return Toc((
        TocItem('part1', 'part1/index.html', **_children_if(toc_expansion > 1, Toc((
            TocItem('chapter1', 'part1/chapter1/index.html', **_children_if(toc_expansion > 2, Toc((
                TocItem('section1', 'part1/chapter1/section1/index.html', **_children_if(toc_expansion > 3, Toc((
                    TocItem('article1', 'part1/chapter1/section1/article1.html'),
                    TocItem('article2', 'part1/chapter1/section1/article2.html'),
                )))),
                TocItem('section2', 'part1/chapter1/section2/index.html', **_children_if(toc_expansion > 3, Toc((
                    TocItem('article1', 'part1/chapter1/section2/article1.html'),
                    TocItem('article2', 'part1/chapter1/section2/article2.html'),
                )))),
            )))),
            TocItem('chapter2', 'part1/chapter2/index.html', **_children_if(toc_expansion > 2, Toc((
                TocItem('section1', 'part1/chapter2/section1/index.html', **_children_if(toc_expansion > 3, Toc((
                    TocItem('article1', 'part1/chapter2/section1/article1.html'),
                    TocItem('article2', 'part1/chapter2/section1/article2.html'),
                )))),
                TocItem('section2', 'part1/chapter2/section2/index.html', **_children_if(toc_expansion > 3, Toc((
                    TocItem('article1', 'part1/chapter2/section2/article1.html'),
                    TocItem('article2', 'part1/chapter2/section2/article2.html'),
                )))),
            )))),
        )))),
        TocItem('part2', 'part2/index.html', **_children_if(toc_expansion > 1, Toc((
            TocItem('chapter1', 'part2/chapter1/index.html', **_children_if(toc_expansion > 2, Toc((
                TocItem('section1', 'part2/chapter1/section1/index.html', **_children_if(toc_expansion > 3, Toc((
                    TocItem('article1', 'part2/chapter1/section1/article1.html'),
                    TocItem('article2', 'part2/chapter1/section1/article2.html'),
                )))),
                TocItem('section2', 'part2/chapter1/section2/index.html', **_children_if(toc_expansion > 3, Toc((
                    TocItem('article1', 'part2/chapter1/section2/article1.html'),
                    TocItem('article2', 'part2/chapter1/section2/article2.html'),
                )))),
            )))),
            TocItem('chapter2', 'part2/chapter2/index.html', **_children_if(toc_expansion > 2, Toc((
                TocItem('section1', 'part2/chapter2/section1/index.html', **_children_if(toc_expansion > 3, Toc((
                    TocItem('article1', 'part2/chapter2/section1/article1.html'),
                    TocItem('article2', 'part2/chapter2/section1/article2.html'),
                )))),
                TocItem('section2', 'part2/chapter2/section2/index.html', **_children_if(toc_expansion > 3, Toc((
                    TocItem('article1', 'part2/chapter2/section2/article1.html'),
                    TocItem('article2', 'part2/chapter2/section2/article2.html'),
                )))),
            )))),
        )))),
    ))


def expected_paths_from_p1(toc_expansion: int | float) -> Toc:
    return Toc((
        TocItem('chapter1', 'chapter1/index.html', **_children_if(toc_expansion > 1, Toc((
            TocItem('section1', 'chapter1/section1/index.html', **_children_if(toc_expansion > 2, Toc((
                TocItem('article1', 'chapter1/section1/article1.html'),
                TocItem('article2', 'chapter1/section1/article2.html'),
            )))),
            TocItem('section2', 'chapter1/section2/index.html', **_children_if(toc_expansion > 2, Toc((
                TocItem('article1', 'chapter1/section2/article1.html'),
                TocItem('article2', 'chapter1/section2/article2.html'),
            )))),
        )))),
        TocItem('chapter2', 'chapter2/index.html', **_children_if(toc_expansion > 1, Toc((
            TocItem('section1', 'chapter2/section1/index.html', **_children_if(toc_expansion > 2, Toc((
                TocItem('article1', 'chapter2/section1/article1.html'),
                TocItem('article2', 'chapter2/section1/article2.html'),
            )))),
            TocItem('section2', 'chapter2/section2/index.html', **_children_if(toc_expansion > 2, Toc((
                TocItem('article1', 'chapter2/section2/article1.html'),
                TocItem('article2', 'chapter2/section2/article2.html'),
            )))),
        )))),
    ))


def expected_paths_from_p1c1(toc_expansion: int | float) -> Toc:
    return Toc((
        TocItem('section1', 'section1/index.html', **_children_if(toc_expansion > 1, Toc((
            TocItem('article1', 'section1/article1.html'),
            TocItem('article2', 'section1/article2.html'),
        )))),
        TocItem('section2', 'section2/index.html', **_children_if(toc_expansion > 1, Toc((
            TocItem('article1', 'section2/article1.html'),
            TocItem('article2', 'section2/article2.html'),
        )))),
    ))


def expected_paths_from_p1c1s1(toc_expansion: int | float) -> Toc:
    return Toc((
        TocItem('article1', 'article1.html'),
        TocItem('article2', 'article2.html'),
    ))


def expected_paths_from_p1c1s1a1(toc_expansion: int | float) -> Toc:
    return Toc()


def _children_if(value: bool, children: list[TocItem]):
    return dict(children=children) if value else dict(is_collapsed=True)


if __name__ == '__main__':
    main()

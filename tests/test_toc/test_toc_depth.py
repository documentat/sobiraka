import re
from math import inf
from tempfile import TemporaryDirectory
from unittest import main
from unittest.mock import Mock

from bs4 import BeautifulSoup
from bs4.formatter import Formatter

from abstracttests.projecttestcase import ProjectTestCase
from helpers import assertNoDiff
from sobiraka.models import FileSystem, IndexPage, Page, Project, Volume
from sobiraka.models.config import CombinedToc, Config, Config_HTML
from sobiraka.processing import WebBuilder
from sobiraka.processing.toc import Toc, TocItem, toc
from sobiraka.utils import AbsolutePath, RelativePath

"""
Test that:
- `config.html.toc_depth` affects which items are included in the TOC,
- items with skipped children have the `is_collapsed` property set to True.
"""


class AbstractTestTocDepth(ProjectTestCase[WebBuilder]):
    toc_depth: int | float

    async def asyncSetUp(self):
        self.output = AbsolutePath(self.enterContext(TemporaryDirectory(prefix='sobiraka-test-')))
        await super().asyncSetUp()

    def _init_project(self) -> Project:
        fs = Mock(FileSystem)
        config = Config(html=Config_HTML(toc_depth=self.toc_depth))
        return Project(fs, {
            RelativePath('src'): Volume(config, dataset_paths()),
        })

    def _init_processor(self):
        return WebBuilder(self.project, self.output)

    async def test_toc_depth(self):
        data = {
            RelativePath('0-index.md'): expected_paths_from_root(self.toc_depth),
            RelativePath('part1/0-index.md'): expected_paths_from_p1(self.toc_depth),
            RelativePath('part1/chapter1/0-index.md'): expected_paths_from_p1c1(self.toc_depth),
            RelativePath('part1/chapter1/section1/0-index.md'): expected_paths_from_p1c1s1(self.toc_depth),
            RelativePath('part1/chapter1/section1/article1.md'): expected_paths_from_p1c1s1a1(self.toc_depth),
        }
        for path, expected in data.items():
            page = self.project.get_volume().pages_by_path[path]
            with self.subTest(page):
                actual = toc(page,
                             processor=self.processor,
                             toc_depth=self.toc_depth,
                             combined_toc=CombinedToc.NEVER,
                             current_page=page)
                self.assertEqual(expected, actual)

    async def test_toc_depth_rendered(self):
        data = {
            RelativePath('0-index.md'): 'from-root.html',
            RelativePath('part1/chapter1/section1/article1.md'): 'from-nonroot.html',
        }
        for path, name in data.items():
            page = self.project.get_volume().pages_by_path[path]
            with self.subTest(page):
                expected_file = AbsolutePath(__file__).parent / 'expected' / str(self.toc_depth) / name

                expected = expected_file.read_text('utf-8')
                expected = BeautifulSoup(expected, 'html.parser').prettify(
                    formatter=Formatter(Formatter.HTML, indent=2))
                expected = re.sub(r'<(a|strong)([^>]*)>\n\s+([^>]+)\n\s+</\1>', r'<\1\2>\3</\1>', expected)

                actual = toc(self.project.get_volume(),
                             processor=self.processor,
                             toc_depth=self.toc_depth,
                             combined_toc=CombinedToc.NEVER,
                             current_page=page)
                actual = str(actual)
                actual = BeautifulSoup(actual, 'html.parser').prettify(formatter=Formatter(Formatter.HTML, indent=2))
                actual = re.sub(r'<(a|strong)([^>]*)>\n\s+([^>]+)\n\s+</\1>', r'<\1\2>\3</\1>', actual)

                assertNoDiff(expected.splitlines(), actual.splitlines())


class TestTocDepth_1(AbstractTestTocDepth):
    toc_depth = 1


class TestTocDepth_2(AbstractTestTocDepth):
    toc_depth = 2


class TestTocDepth_3(AbstractTestTocDepth):
    toc_depth = 3


class TestTocDepth_Infinity(AbstractTestTocDepth):
    toc_depth = inf


del ProjectTestCase, AbstractTestTocDepth


################################################################################

def dataset_paths() -> dict[RelativePath, Page]:
    return {
        RelativePath() / f'0-index.md': IndexPage('# root'),
        RelativePath() / 'part1' / f'0-index.md': IndexPage('# part1'),
        RelativePath() / 'part1' / 'chapter1' / f'0-index.md': IndexPage('# chapter1'),
        RelativePath() / 'part1' / 'chapter1' / 'section1' / f'0-index.md': IndexPage('# section1'),
        RelativePath() / 'part1' / 'chapter1' / 'section1' / f'article1.md': Page('# article1'),
        RelativePath() / 'part1' / 'chapter1' / 'section1' / f'article2.md': Page('# article2'),
        RelativePath() / 'part1' / 'chapter1' / 'section2' / f'0-index.md': IndexPage('# section2'),
        RelativePath() / 'part1' / 'chapter1' / 'section2' / f'article1.md': Page('# article1'),
        RelativePath() / 'part1' / 'chapter1' / 'section2' / f'article2.md': Page('# article2'),
        RelativePath() / 'part1' / 'chapter2' / f'0-index.md': IndexPage('# chapter2'),
        RelativePath() / 'part1' / 'chapter2' / 'section1' / f'0-index.md': IndexPage('# section1'),
        RelativePath() / 'part1' / 'chapter2' / 'section1' / f'article1.md': Page('# article1'),
        RelativePath() / 'part1' / 'chapter2' / 'section1' / f'article2.md': Page('# article2'),
        RelativePath() / 'part1' / 'chapter2' / 'section2' / f'0-index.md': IndexPage('# section2'),
        RelativePath() / 'part1' / 'chapter2' / 'section2' / f'article1.md': Page('# article1'),
        RelativePath() / 'part1' / 'chapter2' / 'section2' / f'article2.md': Page('# article2'),
        RelativePath() / 'part2' / f'0-index.md': IndexPage('# part2'),
        RelativePath() / 'part2' / 'chapter1' / f'0-index.md': IndexPage('# chapter1'),
        RelativePath() / 'part2' / 'chapter1' / 'section1' / f'0-index.md': IndexPage('# section1'),
        RelativePath() / 'part2' / 'chapter1' / 'section1' / f'article1.md': Page('# article1'),
        RelativePath() / 'part2' / 'chapter1' / 'section1' / f'article2.md': Page('# article2'),
        RelativePath() / 'part2' / 'chapter1' / 'section2' / f'0-index.md': IndexPage('# section2'),
        RelativePath() / 'part2' / 'chapter1' / 'section2' / f'article1.md': Page('# article1'),
        RelativePath() / 'part2' / 'chapter1' / 'section2' / f'article2.md': Page('# article2'),
        RelativePath() / 'part2' / 'chapter2' / f'0-index.md': IndexPage('# chapter2'),
        RelativePath() / 'part2' / 'chapter2' / 'section1' / f'0-index.md': IndexPage('# section1'),
        RelativePath() / 'part2' / 'chapter2' / 'section1' / f'article1.md': Page('# article1'),
        RelativePath() / 'part2' / 'chapter2' / 'section1' / f'article2.md': Page('# article2'),
        RelativePath() / 'part2' / 'chapter2' / 'section2' / f'0-index.md': IndexPage('# section2'),
        RelativePath() / 'part2' / 'chapter2' / 'section2' / f'article1.md': Page('# article1'),
        RelativePath() / 'part2' / 'chapter2' / 'section2' / f'article2.md': Page('# article2'),
    }


def expected_paths_from_root(toc_depth: int | float) -> Toc:
    return Toc(
        TocItem('part1', 'part1/index.html', **_children_if(toc_depth > 1, Toc(
            TocItem('chapter1', 'part1/chapter1/index.html', **_children_if(toc_depth > 2, Toc(
                TocItem('section1', 'part1/chapter1/section1/index.html', **_children_if(toc_depth > 3, Toc(
                    TocItem('article1', 'part1/chapter1/section1/article1.html'),
                    TocItem('article2', 'part1/chapter1/section1/article2.html'),
                ))),
                TocItem('section2', 'part1/chapter1/section2/index.html', **_children_if(toc_depth > 3, Toc(
                    TocItem('article1', 'part1/chapter1/section2/article1.html'),
                    TocItem('article2', 'part1/chapter1/section2/article2.html'),
                ))),
            ))),
            TocItem('chapter2', 'part1/chapter2/index.html', **_children_if(toc_depth > 2, Toc(
                TocItem('section1', 'part1/chapter2/section1/index.html', **_children_if(toc_depth > 3, Toc(
                    TocItem('article1', 'part1/chapter2/section1/article1.html'),
                    TocItem('article2', 'part1/chapter2/section1/article2.html'),
                ))),
                TocItem('section2', 'part1/chapter2/section2/index.html', **_children_if(toc_depth > 3, Toc(
                    TocItem('article1', 'part1/chapter2/section2/article1.html'),
                    TocItem('article2', 'part1/chapter2/section2/article2.html'),
                ))),
            ))),
        ))),
        TocItem('part2', 'part2/index.html', **_children_if(toc_depth > 1, Toc(
            TocItem('chapter1', 'part2/chapter1/index.html', **_children_if(toc_depth > 2, Toc(
                TocItem('section1', 'part2/chapter1/section1/index.html', **_children_if(toc_depth > 3, Toc(
                    TocItem('article1', 'part2/chapter1/section1/article1.html'),
                    TocItem('article2', 'part2/chapter1/section1/article2.html'),
                ))),
                TocItem('section2', 'part2/chapter1/section2/index.html', **_children_if(toc_depth > 3, Toc(
                    TocItem('article1', 'part2/chapter1/section2/article1.html'),
                    TocItem('article2', 'part2/chapter1/section2/article2.html'),
                ))),
            ))),
            TocItem('chapter2', 'part2/chapter2/index.html', **_children_if(toc_depth > 2, Toc(
                TocItem('section1', 'part2/chapter2/section1/index.html', **_children_if(toc_depth > 3, Toc(
                    TocItem('article1', 'part2/chapter2/section1/article1.html'),
                    TocItem('article2', 'part2/chapter2/section1/article2.html'),
                ))),
                TocItem('section2', 'part2/chapter2/section2/index.html', **_children_if(toc_depth > 3, Toc(
                    TocItem('article1', 'part2/chapter2/section2/article1.html'),
                    TocItem('article2', 'part2/chapter2/section2/article2.html'),
                ))),
            ))),
        ))),
    )


def expected_paths_from_p1(toc_depth: int | float) -> Toc:
    return Toc(
        TocItem('chapter1', 'chapter1/index.html', **_children_if(toc_depth > 1, Toc(
            TocItem('section1', 'chapter1/section1/index.html', **_children_if(toc_depth > 2, Toc(
                TocItem('article1', 'chapter1/section1/article1.html'),
                TocItem('article2', 'chapter1/section1/article2.html'),
            ))),
            TocItem('section2', 'chapter1/section2/index.html', **_children_if(toc_depth > 2, Toc(
                TocItem('article1', 'chapter1/section2/article1.html'),
                TocItem('article2', 'chapter1/section2/article2.html'),
            ))),
        ))),
        TocItem('chapter2', 'chapter2/index.html', **_children_if(toc_depth > 1, Toc(
            TocItem('section1', 'chapter2/section1/index.html', **_children_if(toc_depth > 2, Toc(
                TocItem('article1', 'chapter2/section1/article1.html'),
                TocItem('article2', 'chapter2/section1/article2.html'),
            ))),
            TocItem('section2', 'chapter2/section2/index.html', **_children_if(toc_depth > 2, Toc(
                TocItem('article1', 'chapter2/section2/article1.html'),
                TocItem('article2', 'chapter2/section2/article2.html'),
            ))),
        ))),
    )


def expected_paths_from_p1c1(toc_depth: int | float) -> Toc:
    return Toc(
        TocItem('section1', 'section1/index.html', **_children_if(toc_depth > 1, Toc(
            TocItem('article1', 'section1/article1.html'),
            TocItem('article2', 'section1/article2.html'),
        ))),
        TocItem('section2', 'section2/index.html', **_children_if(toc_depth > 1, Toc(
            TocItem('article1', 'section2/article1.html'),
            TocItem('article2', 'section2/article2.html'),
        ))),
    )


def expected_paths_from_p1c1s1(toc_depth: int | float) -> Toc:
    return Toc(
        TocItem('article1', 'article1.html'),
        TocItem('article2', 'article2.html'),
    )


def expected_paths_from_p1c1s1a1(toc_depth: int | float) -> Toc:
    return Toc()


def _children_if(value: bool, children: list[TocItem]):
    return dict(children=children) if value else dict(is_collapsed=True)


if __name__ == '__main__':
    main()

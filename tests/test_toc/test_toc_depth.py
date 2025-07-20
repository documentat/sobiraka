import re
from math import inf
from tempfile import TemporaryDirectory
from unittest import main

from bs4 import BeautifulSoup
from bs4.formatter import Formatter

from abstracttests.projecttestcase import ProjectTestCase
from helpers import assertNoDiff
from helpers.fakeproject import FakeDocument, FakeProject
from sobiraka.models import Project
from sobiraka.models.config import CombinedToc, Config, Config_Paths, Config_Web
from sobiraka.processing.toc import CollapsedToc, Toc, TocItem, toc
from sobiraka.processing.web import WebBuilder
from sobiraka.utils import AbsolutePath, RelativePath


class AbstractTestTocDepth(ProjectTestCase[WebBuilder]):
    toc_depth: int | float

    async def asyncSetUp(self):
        # pylint: disable=consider-using-with
        self.output = AbsolutePath(self.enterContext(TemporaryDirectory(prefix='sobiraka-test-')))
        await super().asyncSetUp()

    def _init_project(self) -> Project:
        config = Config(
            paths=Config_Paths(root=RelativePath('src')),
            web=Config_Web(toc_depth=self.toc_depth),
        )
        return FakeProject({
            'src': FakeDocument(config, dataset_paths()),
        })

    def _init_builder(self):
        return WebBuilder(self.project, self.output)

    async def test_toc_depth(self):
        data = {
            '/': expected_paths_from_root(self.toc_depth),
            '/part1/': expected_paths_from_p1(self.toc_depth),
            '/part1/chapter1/': expected_paths_from_p1c1(self.toc_depth),
            '/part1/chapter1/section1/': expected_paths_from_p1c1s1(),
            '/part1/chapter1/section1/article1': expected_paths_from_p1c1s1a1(),
        }
        for location, expected in data.items():
            page = self.project.get_document().get_page_by_location(location)
            with self.subTest(page):
                actual = toc(page,
                             builder=self.builder,
                             toc_depth=self.toc_depth,
                             combined_toc=CombinedToc.NEVER,
                             current_page=page)
                self.assertEqual(expected, actual)

    async def test_toc_depth_rendered(self):
        data = {
            '/': 'from-root.html',
            '/part1/chapter1/section1/article1': 'from-nonroot.html',
        }
        for location, name in data.items():
            page = self.project.get_document().get_page_by_location(location)
            with self.subTest(page):
                expected_file = AbsolutePath(__file__).parent / 'expected' / str(self.toc_depth) / name

                expected = expected_file.read_text('utf-8')
                expected = BeautifulSoup(expected, 'html.parser').prettify(
                    formatter=Formatter(Formatter.HTML, indent=2))
                expected = re.sub(r'<(a|strong)([^>]*)>\n\s+([^>]+)\n\s+</\1>', r'<\1\2>\3</\1>', expected)

                actual = toc(self.project.get_document().root_page,
                             builder=self.builder,
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

def dataset_paths() -> dict[str, str]:
    return {
        '0-index.md': '# root',
        'part1/0-index.md': '# part1',
        'part1/chapter1/0-index.md': '# chapter1',
        'part1/chapter1/section1/0-index.md': '# section1',
        'part1/chapter1/section1/article1.md': '# article1',
        'part1/chapter1/section1/article2.md': '# article2',
        'part1/chapter1/section2/0-index.md': '# section2',
        'part1/chapter1/section2/article1.md': '# article1',
        'part1/chapter1/section2/article2.md': '# article2',
        'part1/chapter2/0-index.md': '# chapter2',
        'part1/chapter2/section1/0-index.md': '# section1',
        'part1/chapter2/section1/article1.md': '# article1',
        'part1/chapter2/section1/article2.md': '# article2',
        'part1/chapter2/section2/0-index.md': '# section2',
        'part1/chapter2/section2/article1.md': '# article1',
        'part1/chapter2/section2/article2.md': '# article2',
        'part2/0-index.md': '# part2',
        'part2/chapter1/0-index.md': '# chapter1',
        'part2/chapter1/section1/0-index.md': '# section1',
        'part2/chapter1/section1/article1.md': '# article1',
        'part2/chapter1/section1/article2.md': '# article2',
        'part2/chapter1/section2/0-index.md': '# section2',
        'part2/chapter1/section2/article1.md': '# article1',
        'part2/chapter1/section2/article2.md': '# article2',
        'part2/chapter2/0-index.md': '# chapter2',
        'part2/chapter2/section1/0-index.md': '# section1',
        'part2/chapter2/section1/article1.md': '# article1',
        'part2/chapter2/section1/article2.md': '# article2',
        'part2/chapter2/section2/0-index.md': '# section2',
        'part2/chapter2/section2/article1.md': '# article1',
        'part2/chapter2/section2/article2.md': '# article2',
    }


def expected_paths_from_root(toc_depth: int | float) -> Toc:
    return Toc(
        TocItem('part1', 'part1/index.html', children=_children_if(toc_depth > 1, Toc(
            TocItem('chapter1', 'part1/chapter1/index.html', children=_children_if(toc_depth > 2, Toc(
                TocItem('section1', 'part1/chapter1/section1/index.html', children=_children_if(toc_depth > 3, Toc(
                    TocItem('article1', 'part1/chapter1/section1/article1.html'),
                    TocItem('article2', 'part1/chapter1/section1/article2.html'),
                ))),
                TocItem('section2', 'part1/chapter1/section2/index.html', children=_children_if(toc_depth > 3, Toc(
                    TocItem('article1', 'part1/chapter1/section2/article1.html'),
                    TocItem('article2', 'part1/chapter1/section2/article2.html'),
                ))),
            ))),
            TocItem('chapter2', 'part1/chapter2/index.html', children=_children_if(toc_depth > 2, Toc(
                TocItem('section1', 'part1/chapter2/section1/index.html', children=_children_if(toc_depth > 3, Toc(
                    TocItem('article1', 'part1/chapter2/section1/article1.html'),
                    TocItem('article2', 'part1/chapter2/section1/article2.html'),
                ))),
                TocItem('section2', 'part1/chapter2/section2/index.html', children=_children_if(toc_depth > 3, Toc(
                    TocItem('article1', 'part1/chapter2/section2/article1.html'),
                    TocItem('article2', 'part1/chapter2/section2/article2.html'),
                ))),
            ))),
        ))),
        TocItem('part2', 'part2/index.html', children=_children_if(toc_depth > 1, Toc(
            TocItem('chapter1', 'part2/chapter1/index.html', children=_children_if(toc_depth > 2, Toc(
                TocItem('section1', 'part2/chapter1/section1/index.html', children=_children_if(toc_depth > 3, Toc(
                    TocItem('article1', 'part2/chapter1/section1/article1.html'),
                    TocItem('article2', 'part2/chapter1/section1/article2.html'),
                ))),
                TocItem('section2', 'part2/chapter1/section2/index.html', children=_children_if(toc_depth > 3, Toc(
                    TocItem('article1', 'part2/chapter1/section2/article1.html'),
                    TocItem('article2', 'part2/chapter1/section2/article2.html'),
                ))),
            ))),
            TocItem('chapter2', 'part2/chapter2/index.html', children=_children_if(toc_depth > 2, Toc(
                TocItem('section1', 'part2/chapter2/section1/index.html', children=_children_if(toc_depth > 3, Toc(
                    TocItem('article1', 'part2/chapter2/section1/article1.html'),
                    TocItem('article2', 'part2/chapter2/section1/article2.html'),
                ))),
                TocItem('section2', 'part2/chapter2/section2/index.html', children=_children_if(toc_depth > 3, Toc(
                    TocItem('article1', 'part2/chapter2/section2/article1.html'),
                    TocItem('article2', 'part2/chapter2/section2/article2.html'),
                ))),
            ))),
        ))),
    )


def expected_paths_from_p1(toc_depth: int | float) -> Toc:
    return Toc(
        TocItem('chapter1', 'chapter1/index.html', children=_children_if(toc_depth > 1, Toc(
            TocItem('section1', 'chapter1/section1/index.html', children=_children_if(toc_depth > 2, Toc(
                TocItem('article1', 'chapter1/section1/article1.html'),
                TocItem('article2', 'chapter1/section1/article2.html'),
            ))),
            TocItem('section2', 'chapter1/section2/index.html', children=_children_if(toc_depth > 2, Toc(
                TocItem('article1', 'chapter1/section2/article1.html'),
                TocItem('article2', 'chapter1/section2/article2.html'),
            ))),
        ))),
        TocItem('chapter2', 'chapter2/index.html', children=_children_if(toc_depth > 1, Toc(
            TocItem('section1', 'chapter2/section1/index.html', children=_children_if(toc_depth > 2, Toc(
                TocItem('article1', 'chapter2/section1/article1.html'),
                TocItem('article2', 'chapter2/section1/article2.html'),
            ))),
            TocItem('section2', 'chapter2/section2/index.html', children=_children_if(toc_depth > 2, Toc(
                TocItem('article1', 'chapter2/section2/article1.html'),
                TocItem('article2', 'chapter2/section2/article2.html'),
            ))),
        ))),
    )


def expected_paths_from_p1c1(toc_depth: int | float) -> Toc:
    return Toc(
        TocItem('section1', 'section1/index.html', children=_children_if(toc_depth > 1, Toc(
            TocItem('article1', 'section1/article1.html'),
            TocItem('article2', 'section1/article2.html'),
        ))),
        TocItem('section2', 'section2/index.html', children=_children_if(toc_depth > 1, Toc(
            TocItem('article1', 'section2/article1.html'),
            TocItem('article2', 'section2/article2.html'),
        ))),
    )


def expected_paths_from_p1c1s1() -> Toc:
    return Toc(
        TocItem('article1', 'article1.html'),
        TocItem('article2', 'article2.html'),
    )


def expected_paths_from_p1c1s1a1() -> Toc:
    return Toc()


def _children_if(value: bool, children: list[TocItem]) -> Toc | CollapsedToc:
    return children if value else CollapsedToc()


if __name__ == '__main__':
    main()

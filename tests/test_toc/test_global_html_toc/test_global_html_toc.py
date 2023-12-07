import re
from math import inf
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import main
from unittest.mock import Mock

from bs4 import BeautifulSoup
from bs4.formatter import Formatter

from abstracttests.projecttestcase import ProjectTestCase
from helpers import assertNoDiff
from sobiraka.models import FileSystem, Project, Volume
from sobiraka.models.config import Config, Config_HTML
from sobiraka.processing import HtmlBuilder
from sobiraka.processing.htmlbuilder import GlobalToc_HTML
from test_toc.datasets import dataset_expected_items, dataset_paths


class AbstractTestGlobalHtmlToc(ProjectTestCase):
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

    async def test_get_root(self):
        expected = self.project.pages_by_path[Path('src/0-index.md')]
        toc = GlobalToc_HTML(self.processor, self.project.get_volume(), NotImplemented)
        actual = toc.get_root()
        self.assertIs(expected, actual)

    async def test_global_toc_items(self):
        expected = dataset_expected_items(self.toc_expansion)
        actual = await GlobalToc_HTML(self.processor, self.project.get_volume(), self.project.pages[0]).items()
        self.assertEqual(expected, actual)

    async def test_global_toc_rendered(self):
        for path, name in ((Path('0-index.md'), 'from-root.html'),
                           (Path('part1/chapter1/section1/article1.md'), 'from-nonroot.html')):
            page = self.project.get_volume().pages_by_path[path]
            with self.subTest(page):
                expected_file = Path(__file__).parent / 'expected' / str(self.toc_expansion) / name

                expected = expected_file.read_text('utf-8')
                expected = BeautifulSoup(expected, 'html.parser').prettify(
                    formatter=Formatter(Formatter.HTML, indent=2))
                expected = re.sub(r'<(a|strong)([^>]*)>\n\s+([^>]+)\n\s+</\1>', r'<\1\2>\3</\1>', expected)

                actual = await GlobalToc_HTML(self.processor, page.volume, page)()
                actual = BeautifulSoup(actual, 'html.parser').prettify(formatter=Formatter(Formatter.HTML, indent=2))
                actual = re.sub(r'<(a|strong)([^>]*)>\n\s+([^>]+)\n\s+</\1>', r'<\1\2>\3</\1>', actual)

                assertNoDiff(expected.splitlines(), actual.splitlines())


class TestGlobalHtmlToc_1(AbstractTestGlobalHtmlToc):
    toc_expansion = 1


class TestGlobalHtmlToc_2(AbstractTestGlobalHtmlToc):
    toc_expansion = 2


class TestGlobalHtmlToc_3(AbstractTestGlobalHtmlToc):
    toc_expansion = 3


class TestGlobalHtmlToc_Infinity(AbstractTestGlobalHtmlToc):
    toc_expansion = inf


del ProjectTestCase, AbstractTestGlobalHtmlToc

if __name__ == '__main__':
    main()

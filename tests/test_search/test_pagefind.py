from abc import ABCMeta
from textwrap import dedent
from unittest import main
from unittest.mock import MagicMock, Mock, call, patch

from abstracttests.abstracttestwithrt import AbstractTestWithRtTmp
from abstracttests.projecttestcase import ProjectTestCase
from sobiraka.models import FileSystem, Page, PageStatus, Project, Volume
from sobiraka.models.config import Config_Search_LinkTarget, Config_Web_Search
from sobiraka.processing import WebBuilder
from sobiraka.processing.web.search import PagefindIndexer
from sobiraka.runtime import RT
from sobiraka.utils import RelativePath


@patch(f'{PagefindIndexer.__module__}.{PagefindIndexer.__qualname__}._add_record')
class AbstractTestPagefindIndexer(ProjectTestCase[WebBuilder], AbstractTestWithRtTmp, metaclass=ABCMeta):
    REQUIRE = PageStatus.PROCESS4

    LINK_TARGET = Config_Search_LinkTarget.H1
    EXPECTED: tuple[call, ...]

    def _init_processor(self):
        return WebBuilder(self.project, RT.TMP / 'build')

    async def test_add_record(self, mock: MagicMock):
        indexer = PagefindIndexer(self.processor, self.project.get_volume(), RT.TMP / 'build' / 'pagefind')
        indexer.search_config = Config_Web_Search(link_target=self.LINK_TARGET)
        await indexer.initialize()
        for page in self.project.pages:
            await indexer.add_page(page)
        await indexer.finalize()

        for expected_call in self.EXPECTED:
            with self.subTest(expected_call.kwargs['url'].replace('.html', '')):
                self.assertIn(expected_call, mock.mock_calls)

        self.assertEqual(len(self.EXPECTED), len(mock.mock_calls))


class TestPagefindIndexer_Basic(AbstractTestPagefindIndexer):
    def _init_project(self) -> Project:
        return Project(Mock(FileSystem), {
            RelativePath('src'): Volume({

                RelativePath('formatting.md'): Page(dedent('''
                    # Page with formatting
                    Normal, _italic_, **bold**, _**bold italic**_!
                ''')),

                RelativePath('links.md'): Page(dedent('''
                    # Page with links
                    Internal link 1: [formatting](formatting.md).
                    Internal link 2: [](formatting.md).
                    External link: [visit my website](https://example.com/).
                ''')),
            }),
        })

    EXPECTED = (
        call(
            url='index.html',
            title='',
            content='Page with formatting\nPage with links\n'),
        call(
            url='formatting.html',
            title='Page with formatting',
            content='Normal, italic, bold, bold italic!\n'),
        call(
            url='links.html',
            title='Page with links',
            content='Internal link 1: formatting.\n'
                    'Internal link 2: Page with formatting.\n'
                    'External link: visit my website.\n'),
    )


class AbstractTestPagefindIndexer_UpToLevel(AbstractTestPagefindIndexer, metaclass=ABCMeta):
    def _init_project(self) -> Project:
        return Project(Mock(FileSystem), {
            RelativePath('src'): Volume({
                RelativePath(): Page(dedent('''
                    # H1
                    text1
                    
                    ## H2
                    text2
                    
                    ### H3
                    text3
                    
                    #### H4
                    text4
                    
                    ##### H5
                    text5
                    
                    ###### H6
                    text6
                ''')),
            }),
        })


class TestPagefindIndexer_UpToLevel_1(AbstractTestPagefindIndexer_UpToLevel):
    LINK_TARGET = Config_Search_LinkTarget.H1
    EXPECTED = (
        call(url='index.html', title='H1',
             content='text1\nH2\ntext2\nH3\ntext3\nH4\ntext4\nH5\ntext5\nH6\ntext6\n'),
    )


class TestPagefindIndexer_UpToLevel_2(AbstractTestPagefindIndexer_UpToLevel):
    LINK_TARGET = Config_Search_LinkTarget.H2
    EXPECTED = (
        call(url='index.html', title='H1',
             content='text1\n'),
        call(url='index.html#h2', title='H1 » H2',
             content='text2\nH3\ntext3\nH4\ntext4\nH5\ntext5\nH6\ntext6\n'),
    )


class TestPagefindIndexer_UpToLevel_3(AbstractTestPagefindIndexer_UpToLevel):
    LINK_TARGET = Config_Search_LinkTarget.H3
    EXPECTED = (
        call(url='index.html', title='H1',
             content='text1\n'),
        call(url='index.html#h2', title='H1 » H2',
             content='text2\n'),
        call(url='index.html#h3', title='H1 » H3',
             content='text3\nH4\ntext4\nH5\ntext5\nH6\ntext6\n'),
    )


class TestPagefindIndexer_UpToLevel_4(AbstractTestPagefindIndexer_UpToLevel):
    LINK_TARGET = Config_Search_LinkTarget.H4
    EXPECTED = (
        call(url='index.html', title='H1',
             content='text1\n'),
        call(url='index.html#h2', title='H1 » H2',
             content='text2\n'),
        call(url='index.html#h3', title='H1 » H3',
             content='text3\n'),
        call(url='index.html#h4', title='H1 » H4',
             content='text4\nH5\ntext5\nH6\ntext6\n'),
    )


class TestPagefindIndexer_UpToLevel_5(AbstractTestPagefindIndexer_UpToLevel):
    LINK_TARGET = Config_Search_LinkTarget.H5
    EXPECTED = (
        call(url='index.html', title='H1',
             content='text1\n'),
        call(url='index.html#h2', title='H1 » H2',
             content='text2\n'),
        call(url='index.html#h3', title='H1 » H3',
             content='text3\n'),
        call(url='index.html#h4', title='H1 » H4',
             content='text4\n'),
        call(url='index.html#h5', title='H1 » H5',
             content='text5\nH6\ntext6\n'),
    )


class TestPagefindIndexer_UpToLevel_6(AbstractTestPagefindIndexer_UpToLevel):
    LINK_TARGET = Config_Search_LinkTarget.H6
    EXPECTED = (
        call(url='index.html', title='H1',
             content='text1\n'),
        call(url='index.html#h2', title='H1 » H2',
             content='text2\n'),
        call(url='index.html#h3', title='H1 » H3',
             content='text3\n'),
        call(url='index.html#h4', title='H1 » H4',
             content='text4\n'),
        call(url='index.html#h5', title='H1 » H5',
             content='text5\n'),
        call(url='index.html#h6', title='H1 » H6',
             content='text6\n'),
    )


del ProjectTestCase, AbstractTestPagefindIndexer, AbstractTestPagefindIndexer_UpToLevel

if __name__ == '__main__':
    main()

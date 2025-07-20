from abc import ABCMeta
from unittest import main
from unittest.mock import Mock, call

from typing_extensions import override

from abstracttests.abstracttestwithrt import AbstractTestWithRtTmp
from abstracttests.projecttestcase import ProjectTestCase
from helpers.fakeproject import FakeDocument, FakeProject
from sobiraka.models import Document, Project, Status
from sobiraka.models.config import Config, Config_Paths, Config_Search_LinkTarget, Config_Web, Config_Web_Search, \
    SearchIndexerName
from sobiraka.processing.web import WebBuilder
from sobiraka.processing.web.search import PagefindIndexer
from sobiraka.runtime import RT
from sobiraka.utils import RelativePath


class WebBuilderWithMockIndexer(WebBuilder):
    # pylint: disable=subclassed-final-class

    @override
    async def prepare_search_indexer(self, document: Document):
        await super().prepare_search_indexer(document)

        indexer = self._indexers[document]
        assert isinstance(indexer, PagefindIndexer)
        indexer._add_record = Mock()  # pylint: disable=protected-access


class AbstractTestPagefindIndexer(ProjectTestCase[WebBuilder], AbstractTestWithRtTmp, metaclass=ABCMeta):
    REQUIRE = Status.PROCESS4

    LINK_TARGET = Config_Search_LinkTarget.H1
    EXPECTED: tuple[call, ...]

    @override
    def _init_builder(self):
        return WebBuilderWithMockIndexer(self.project, RT.TMP)

    def _init_config(self) -> Config:
        return Config(
            paths=Config_Paths(
                root=RelativePath('src'),
            ),
            web=Config_Web(
                search=Config_Web_Search(
                    engine=SearchIndexerName.PAGEFIND,
                    link_target=self.LINK_TARGET,
                ),
            ),
        )

    @override
    async def _process(self):
        await self.builder.run()

    async def test_add_record(self):
        # pylint: disable=protected-access
        indexer: PagefindIndexer = self.builder._indexers[self.project.get_document()]
        mock: Mock = indexer._add_record

        for expected_call in self.EXPECTED:
            with self.subTest(expected_call.kwargs['url'].replace('.html', '')):
                self.assertIn(expected_call, mock.mock_calls)

        self.assertEqual(len(self.EXPECTED), len(mock.mock_calls))


class TestPagefindIndexer_Basic(AbstractTestPagefindIndexer):
    def _init_project(self) -> Project:
        return FakeProject({
            'src': FakeDocument(self._init_config(), {
                'index.md': '''
                    # Test Pagefind
                    @toc
                ''',
                'formatting.md': '''
                    # Page with formatting
                    Normal, _italic_, **bold**, _**bold italic**_!
                ''',
                'links.md': '''
                    # Page with links
                    Internal link 1: [formatting](formatting.md).
                    Internal link 2: [](formatting.md).
                    External link: [visit my website](https://example.com/).
                ''',
            }),
        })

    EXPECTED = (
        call(
            url='index.html',
            title='Test Pagefind',
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
        return FakeProject({
            'src': FakeDocument(self._init_config(), {
                'index.md': '''
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
                ''',
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

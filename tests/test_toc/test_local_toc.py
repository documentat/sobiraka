from pathlib import Path
from textwrap import dedent
from unittest import main
from unittest.mock import Mock

from abstracttests.abstracttestwithrt import AbstractTestWithRtPages
from sobiraka.models import FileSystem, Page, Project, Volume
from sobiraka.processing.abstract import Processor
from sobiraka.processing.toc import Toc, TocItem, local_toc


class AbstractTestLocalToc(AbstractTestWithRtPages):
    source: str
    expected: Toc

    async def test_local_toc(self):
        project = Project(Mock(FileSystem), {
            Path('src'): Volume({
                Path('page.md'):
                    (page := Page(dedent(self.source))),
            }),
        })
        await Processor().process1(page)
        actual = local_toc(page, href_prefix='page.html')
        self.assertEqual(self.expected, actual)


class TestLocalToc_Empty(AbstractTestLocalToc):
    source = ''
    expected = Toc()


class TestLocalToc_Linear(AbstractTestLocalToc):
    source = '''
        ## Paragraph 1
        ## Paragraph 2
        ## Paragraph 3
    '''

    expected = Toc((
        TocItem('Paragraph 1', 'page.html#paragraph-1'),
        TocItem('Paragraph 2', 'page.html#paragraph-2'),
        TocItem('Paragraph 3', 'page.html#paragraph-3'),
    ))


class TestLocalToc_Linear_CustomAnchors(AbstractTestLocalToc):
    source = '''
        ## Paragraph 1 {#para1}
        ## Paragraph 2 {#para2}
        ## Paragraph 3 {#para3}
    '''

    expected = Toc((
        TocItem('Paragraph 1', 'page.html#para1'),
        TocItem('Paragraph 2', 'page.html#para2'),
        TocItem('Paragraph 3', 'page.html#para3'),
    ))


class TestLocalToc_Deep(AbstractTestLocalToc):
    source = '''
        ## Paragraph 1
        ### Paragraph 1.1
        #### Paragraph 1.1.1
        #### Paragraph 1.1.2
        ### Paragraph 1.2
        #### Paragraph 1.2.1
        #### Paragraph 1.2.2
        ## Paragraph 2
        ### Paragraph 2.1
        #### Paragraph 2.1.1
        #### Paragraph 2.1.2
        ### Paragraph 2.2
        #### Paragraph 2.2.1
        #### Paragraph 2.2.2
    '''

    expected = Toc((
        TocItem('Paragraph 1', 'page.html#paragraph-1', children=Toc((
            TocItem('Paragraph 1.1', 'page.html#paragraph-1.1', children=Toc((
                TocItem('Paragraph 1.1.1', 'page.html#paragraph-1.1.1'),
                TocItem('Paragraph 1.1.2', 'page.html#paragraph-1.1.2'),
            ))),
            TocItem('Paragraph 1.2', 'page.html#paragraph-1.2', children=Toc((
                TocItem('Paragraph 1.2.1', 'page.html#paragraph-1.2.1'),
                TocItem('Paragraph 1.2.2', 'page.html#paragraph-1.2.2'),
            ))),
        ))),
        TocItem('Paragraph 2', 'page.html#paragraph-2', children=Toc((
            TocItem('Paragraph 2.1', 'page.html#paragraph-2.1', children=Toc((
                TocItem('Paragraph 2.1.1', 'page.html#paragraph-2.1.1'),
                TocItem('Paragraph 2.1.2', 'page.html#paragraph-2.1.2'),
            ))),
            TocItem('Paragraph 2.2', 'page.html#paragraph-2.2', children=Toc((
                TocItem('Paragraph 2.2.1', 'page.html#paragraph-2.2.1'),
                TocItem('Paragraph 2.2.2', 'page.html#paragraph-2.2.2'),
            ))),
        ))),
    ))


class TestLocalToc_Deep_CustomAnchors(AbstractTestLocalToc):
    source = '''
        ## Paragraph 1 {#para1}
        ### Paragraph 1.1 {#para11}
        #### Paragraph 1.1.1 {#para111}
        #### Paragraph 1.1.2 {#para112}
        ### Paragraph 1.2 {#para12}
        #### Paragraph 1.2.1 {#para121}
        #### Paragraph 1.2.2 {#para122}
        ## Paragraph 2 {#para2}
        ### Paragraph 2.1 {#para21}
        #### Paragraph 2.1.1 {#para211}
        #### Paragraph 2.1.2 {#para212}
        ### Paragraph 2.2 {#para22}
        #### Paragraph 2.2.1 {#para221}
        #### Paragraph 2.2.2 {#para222}
    '''

    expected = Toc((
        TocItem('Paragraph 1', 'page.html#para1', children=Toc((
            TocItem('Paragraph 1.1', 'page.html#para11', children=Toc((
                TocItem('Paragraph 1.1.1', 'page.html#para111'),
                TocItem('Paragraph 1.1.2', 'page.html#para112'),
            ))),
            TocItem('Paragraph 1.2', 'page.html#para12', children=Toc((
                TocItem('Paragraph 1.2.1', 'page.html#para121'),
                TocItem('Paragraph 1.2.2', 'page.html#para122'),
            ))),
        ))),
        TocItem('Paragraph 2', 'page.html#para2', children=Toc((
            TocItem('Paragraph 2.1', 'page.html#para21', children=Toc((
                TocItem('Paragraph 2.1.1', 'page.html#para211'),
                TocItem('Paragraph 2.1.2', 'page.html#para212'),
            ))),
            TocItem('Paragraph 2.2', 'page.html#para22', children=Toc((
                TocItem('Paragraph 2.2.1', 'page.html#para221'),
                TocItem('Paragraph 2.2.2', 'page.html#para222'),
            ))),
        ))),
    ))


del AbstractTestLocalToc

if __name__ == '__main__':
    main()

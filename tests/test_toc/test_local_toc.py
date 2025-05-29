from math import inf
from unittest import main

from abstracttests.singlepageprojecttest import SinglePageProjectTest
from sobiraka.models import Status
from sobiraka.processing.toc import Toc, TocItem, local_toc


class AbstractTestLocalToc(SinglePageProjectTest):
    REQUIRE = Status.FINALIZE

    PATH = 'page.md'

    TOC_DEPTH: int | float = inf
    EXPECTED: Toc

    async def test_local_toc(self):
        actual = local_toc(self.page, builder=self.builder, toc_depth=self.TOC_DEPTH)
        self.assertEqual(self.EXPECTED, actual)


class TestLocalToc_Empty(AbstractTestLocalToc):
    SOURCE = ''
    EXPECTED = Toc()


class TestLocalToc_Linear(AbstractTestLocalToc):
    SOURCE = '''
        ## Paragraph 1
        ## Paragraph 2
        ## Paragraph 3
    '''

    EXPECTED = Toc(
        TocItem('Paragraph 1', 'page.md#paragraph-1'),
        TocItem('Paragraph 2', 'page.md#paragraph-2'),
        TocItem('Paragraph 3', 'page.md#paragraph-3'),
    )


class TestLocalToc_Linear_CustomAnchors(AbstractTestLocalToc):
    SOURCE = '''
        ## Paragraph 1 {#para1}
        ## Paragraph 2 {#para2}
        ## Paragraph 3 {#para3}
    '''

    EXPECTED = Toc(
        TocItem('Paragraph 1', 'page.md#para1'),
        TocItem('Paragraph 2', 'page.md#para2'),
        TocItem('Paragraph 3', 'page.md#para3'),
    )


class TestLocalToc_Deep(AbstractTestLocalToc):
    SOURCE = '''
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

    EXPECTED = Toc(
        TocItem('Paragraph 1', 'page.md#paragraph-1', children=Toc(
            TocItem('Paragraph 1.1', 'page.md#paragraph-1.1', children=Toc(
                TocItem('Paragraph 1.1.1', 'page.md#paragraph-1.1.1'),
                TocItem('Paragraph 1.1.2', 'page.md#paragraph-1.1.2'),
            )),
            TocItem('Paragraph 1.2', 'page.md#paragraph-1.2', children=Toc(
                TocItem('Paragraph 1.2.1', 'page.md#paragraph-1.2.1'),
                TocItem('Paragraph 1.2.2', 'page.md#paragraph-1.2.2'),
            )),
        )),
        TocItem('Paragraph 2', 'page.md#paragraph-2', children=Toc(
            TocItem('Paragraph 2.1', 'page.md#paragraph-2.1', children=Toc(
                TocItem('Paragraph 2.1.1', 'page.md#paragraph-2.1.1'),
                TocItem('Paragraph 2.1.2', 'page.md#paragraph-2.1.2'),
            )),
            TocItem('Paragraph 2.2', 'page.md#paragraph-2.2', children=Toc(
                TocItem('Paragraph 2.2.1', 'page.md#paragraph-2.2.1'),
                TocItem('Paragraph 2.2.2', 'page.md#paragraph-2.2.2'),
            )),
        )),
    )


class TestLocalToc_Deep_LimitDepth_3(TestLocalToc_Deep):
    TOC_DEPTH = 3


class TestLocalToc_Deep_LimitDepth_2(TestLocalToc_Deep):
    TOC_DEPTH = 2

    EXPECTED = Toc(
        TocItem('Paragraph 1', 'page.md#paragraph-1', children=Toc(
            TocItem('Paragraph 1.1', 'page.md#paragraph-1.1'),
            TocItem('Paragraph 1.2', 'page.md#paragraph-1.2'),
        )),
        TocItem('Paragraph 2', 'page.md#paragraph-2', children=Toc(
            TocItem('Paragraph 2.1', 'page.md#paragraph-2.1'),
            TocItem('Paragraph 2.2', 'page.md#paragraph-2.2'),
        )),
    )


class TestLocalToc_Deep_LimitDepth_1(TestLocalToc_Deep):
    TOC_DEPTH = 1

    EXPECTED = Toc(
        TocItem('Paragraph 1', 'page.md#paragraph-1'),
        TocItem('Paragraph 2', 'page.md#paragraph-2'),
    )


class TestLocalToc_Deep_CustomAnchors(AbstractTestLocalToc):
    SOURCE = '''
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

    EXPECTED = Toc(
        TocItem('Paragraph 1', 'page.md#para1', children=Toc(
            TocItem('Paragraph 1.1', 'page.md#para11', children=Toc(
                TocItem('Paragraph 1.1.1', 'page.md#para111'),
                TocItem('Paragraph 1.1.2', 'page.md#para112'),
            )),
            TocItem('Paragraph 1.2', 'page.md#para12', children=Toc(
                TocItem('Paragraph 1.2.1', 'page.md#para121'),
                TocItem('Paragraph 1.2.2', 'page.md#para122'),
            )),
        )),
        TocItem('Paragraph 2', 'page.md#para2', children=Toc(
            TocItem('Paragraph 2.1', 'page.md#para21', children=Toc(
                TocItem('Paragraph 2.1.1', 'page.md#para211'),
                TocItem('Paragraph 2.1.2', 'page.md#para212'),
            )),
            TocItem('Paragraph 2.2', 'page.md#para22', children=Toc(
                TocItem('Paragraph 2.2.1', 'page.md#para221'),
                TocItem('Paragraph 2.2.2', 'page.md#para222'),
            )),
        )),
    )


del AbstractTestLocalToc, SinglePageProjectTest

if __name__ == '__main__':
    main()

import unittest
from textwrap import dedent

from abstracttests.singlepageprojecttest import SinglePageProjectTest
from helpers.fakeproject import FakeDocument, FakeProject
from sobiraka.models import Project, Status


class AbstractTestManualToc(SinglePageProjectTest):
    REQUIRE = Status.PROCESS3

    def _init_project(self) -> Project:
        return FakeProject({
            'src': FakeDocument({
                'index.md': dedent(self.SOURCE).strip(),
                'part1/index.md': '# Part 1',
                'part1/chapter1.md': '# Chapter 1.1\n## Section 1.1.1\n## Section 1.1.2',
                'part1/chapter2.md': '# Chapter 1.2\n## Section 1.2.1\n## Section 1.2.2',
                'part2/index.md': '# Part 2',
                'part2/chapter1.md': '# Chapter 2.1\n## Section 2.1.1\n## Section 2.1.2',
                'part2/chapter2.md': '# Chapter 2.2\n## Section 2.2.1\n## Section 2.2.2',
            }),
        })


# ------------------------------------------------------------------------------
# region Global TOC


class TestManualToc_Default(AbstractTestManualToc):
    SOURCE = '''
        @manual-toc
        
        - [](part1)
        - [](part1/chapter1.md)
        - [](part1/chapter2.md)
        - [](part2)
        - [](part2/chapter1.md)
        - [](part2/chapter2.md)
    '''


class TestManualToc_MultiBlock(AbstractTestManualToc):
    SOURCE = '''
        @@manual-toc
        
        [Part one](part1):
        - [](part1/chapter1.md)
        - [](part1/chapter2.md)
        
        [Part two](part2):
        - [](part2/chapter1.md)
        - [](part2/chapter2.md)
        
        @@
    '''


class TestManualToc_Default_Missing(AbstractTestManualToc):
    SOURCE = '''
        @manual-toc
        
        - [](part1)
        - [](part2)
    '''

    EXPECTED_ISSUES = (
        'Missing link in manual TOC: part1/chapter1.md',
        'Missing link in manual TOC: part1/chapter2.md',
        'Missing link in manual TOC: part2/chapter1.md',
        'Missing link in manual TOC: part2/chapter2.md',
    )


class TestManualToc_Unique(AbstractTestManualToc):
    SOURCE = '''
        @manual-toc --unique
        
        - [](part1)
        - [](part1/chapter1.md)
        - [](part1/chapter1.md)
        - [](part1/chapter2.md)
        - [](part2)
        - [](part2)
        - [](part2/chapter1.md)
        - [](part2/chapter2.md)
    '''

    EXPECTED_ISSUES = (
        'Link appears 2 times in manual TOC: part1/chapter1.md',
        'Link appears 2 times in manual TOC: part2/index.md',
    )


class TestManualToc_Depth1(AbstractTestManualToc):
    SOURCE = '''
        @manual-toc --depth 1
        
        - [](part1)
        - [](part2)
    '''


class TestManualToc_Depth1_Missing(AbstractTestManualToc):
    SOURCE = '''
        @manual-toc --depth 1
        
        - [](part1)
    '''

    EXPECTED_ISSUES = (
        'Missing link in manual TOC: part2/index.md',
    )


class TestManualToc_Ordered(AbstractTestManualToc):
    SOURCE = '''
        @manual-toc --ordered
        
        - [](part1)
        - [](part1/chapter2.md)
        - [](part1/chapter1.md)
        - [](part2)
        - [](part2/chapter1.md)
        - [](part2/chapter2.md)
    '''

    EXPECTED_ISSUES = (
        'Wrong order in manual TOC.',
    )


# endregion


# ------------------------------------------------------------------------------
# region Local TOC


class TestManualToc_Local(AbstractTestManualToc):
    SOURCE = '''
        @manual-toc --local
        
        - [](#section-0.1)
        - [](#section-0.1.1)
        - [](#section-0.1.2)
        - [](#section-0.2)
        - [](#section-0.2.1)
        - [](#section-0.2.2)
        - [](#section-0.3)
        - [](#section-0.3.1)
        - [](#section-0.3.2)
        
        ## Section 0.1
        ### Section 0.1.1
        ### Section 0.1.2
        
        ## Section 0.2
        ### Section 0.2.1
        ### Section 0.2.2
        
        ## Section 0.3
        ### Section 0.3.1
        ### Section 0.3.2
    '''


class TestManualToc_Local_Depth1(AbstractTestManualToc):
    SOURCE = '''
        @manual-toc --local --depth 1
        
        - [](#section-0.1)
        - [](#section-0.2)
        - [](#section-0.3)
        
        ## Section 0.1
        ### Section 0.1.1
        ### Section 0.1.2
        
        ## Section 0.2
        ### Section 0.2.1
        ### Section 0.2.2
        
        ## Section 0.3
        ### Section 0.4.1
        ### Section 0.3.2
    '''


# endregion

# ------------------------------------------------------------------------------
# region Combined TOC


class TestManualToc_Combined(AbstractTestManualToc):
    SOURCE = '''
        @manual-toc --combined
        
        - [](part1)
        - [](part1/chapter1.md)
        - [](part1/chapter1.md#section-1.1.1)
        - [](part1/chapter1.md#section-1.1.2)
        - [](part1/chapter2.md)
        - [](part1/chapter2.md#section-1.2.1)
        - [](part1/chapter2.md#section-1.2.2)
        - [](part2)
        - [](part2/chapter1.md)
        - [](part2/chapter1.md#section-2.1.1)
        - [](part2/chapter1.md#section-2.1.2)
        - [](part2/chapter2.md)
        - [](part2/chapter2.md#section-2.2.1)
        - [](part2/chapter2.md#section-2.2.2)
    '''


class TestManualToc_Combined_Missing(AbstractTestManualToc):
    SOURCE = '''
        @manual-toc --combined
        
        - [](part1)
        - [](part1/chapter1.md)
        - [](part1/chapter1.md#section-1.1.1)
        - [](part1/chapter1.md#section-1.1.2)
        - [](part1/chapter2.md)
        - [](part2)
        - [](part2/chapter1.md)
        - [](part2/chapter1.md#section-2.1.1)
        - [](part2/chapter1.md#section-2.1.2)
        - [](part2/chapter2.md)
        - [](part2/chapter2.md#section-2.2.1)
        - [](part2/chapter2.md#section-2.2.2)
    '''

    EXPECTED_ISSUES = (
        'Missing link in manual TOC: part1/chapter2.md#section-1.2.1',
        'Missing link in manual TOC: part1/chapter2.md#section-1.2.2',
    )


# endregion


del AbstractTestManualToc, SinglePageProjectTest

if __name__ == '__main__':
    unittest.main()

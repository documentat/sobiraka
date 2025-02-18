import unittest

from panflute import Block, BulletList, Div, Element, Header, Link, ListItem, Plain, Space, Str

from abstracttests.singlepageprojecttest import SinglePageProjectTest
from helpers import FakeBuilder
from helpers.fakeproject import FakeProject, FakeVolume
from sobiraka.models import Project, Status
from sobiraka.runtime import RT


class AbstractTestTocDirective(SinglePageProjectTest[FakeBuilder]):
    REQUIRE = Status.NUMERATE

    EXPECTED: tuple[Element, ...] = None

    def _init_project(self) -> Project:
        return FakeProject({
            'src': FakeVolume({
                'index.md': self.SOURCE,
                'section1': {
                    'index.md': '# Section 1',
                    'page1.md': '# Page 1.1\n## Paragraph',
                    'page2.md': '# Page 1.2\n## Paragraph',
                },
                'section2': {
                    'index.md': '# Section 2',
                    'page1.md': '# Page 2.1\n## Paragraph',
                    'page2.md': '# Page 2.2\n## Paragraph',
                },
                'section3': {
                    'index.md': '''
                        ---
                        title: Section 3
                        ---
                        # This is the actual title of Section 3
                    ''',
                },
            }),
        })

    async def test_doc(self):
        volume = self.project.get_volume()
        actual = tuple(RT[volume.root_page].doc.content)
        self.assertEqual(self.EXPECTED, actual)


def toc_div(*args: Block) -> Div:
    return Div(*args, classes=['toc'])


# ------------------------------------------------------------------------------


class TestTocDirective(AbstractTestTocDirective):
    SOURCE = '@toc'
    EXPECTED = toc_div(BulletList(
        ListItem(Plain(Link(Str('Section 1'), url='section1/')), BulletList(
            ListItem(Plain(Link(Str('Page 1.1'), url='section1/page1.md'))),
            ListItem(Plain(Link(Str('Page 1.2'), url='section1/page2.md'))),
        )),
        ListItem(Plain(Link(Str('Section 2'), url='section2/')), BulletList(
            ListItem(Plain(Link(Str('Page 2.1'), url='section2/page1.md'))),
            ListItem(Plain(Link(Str('Page 2.2'), url='section2/page2.md'))),
        )),
        ListItem(Plain(Link(Str('Section 3'), url='section3/'))),
    )),


class TestTocDirective_Depth(AbstractTestTocDirective):
    SOURCE = '@toc --depth=1'
    EXPECTED = toc_div(BulletList(
        ListItem(Plain(Link(Str('Section 1'), url='section1/'))),
        ListItem(Plain(Link(Str('Section 2'), url='section2/'))),
        ListItem(Plain(Link(Str('Section 3'), url='section3/'))),
    )),


class TestTocDirective_Local_All(AbstractTestTocDirective):
    SOURCE = '''
        # Introduction
        @toc --local
        
        ## Intro 1
        ### Intro 1.1
        ### Intro 1.2
        ## Intro 2
        ### Intro 2.1
        ### Intro 2.2
    '''
    EXPECTED = (
        Header(Str('Introduction'), level=1),
        toc_div(BulletList(
            ListItem(Plain(Link(Str('Intro 1'), url='#intro-1')), BulletList(
                ListItem(Plain(Link(Str('Intro 1.1'), url='#intro-1.1'))),
                ListItem(Plain(Link(Str('Intro 1.2'), url='#intro-1.2'))),
            )),
            ListItem(Plain(Link(Str('Intro 2'), url='#intro-2')), BulletList(
                ListItem(Plain(Link(Str('Intro 2.1'), url='#intro-2.1'))),
                ListItem(Plain(Link(Str('Intro 2.2'), url='#intro-2.2'))),
            )),
        )),
        Header(Str('Intro'), Space(), Str('1'), level=2, identifier='intro-1'),
        Header(Str('Intro'), Space(), Str('1.1'), level=3, identifier='intro-1.1'),
        Header(Str('Intro'), Space(), Str('1.2'), level=3, identifier='intro-1.2'),
        Header(Str('Intro'), Space(), Str('2'), level=2, identifier='intro-2'),
        Header(Str('Intro'), Space(), Str('2.1'), level=3, identifier='intro-2.1'),
        Header(Str('Intro'), Space(), Str('2.2'), level=3, identifier='intro-2.2'),
    )


class TestTocDirective_Local_Partial(AbstractTestTocDirective):
    SOURCE = '''
        # Introduction
        
        ## Intro 1
        @toc --local
        
        ### Intro 1.1
        ### Intro 1.2
        
        ## Intro 2
        @toc --local

        ### Intro 2.1
        ### Intro 2.2
    '''
    EXPECTED = (
        Header(Str('Introduction'), level=1),

        Header(Str('Intro'), Space(), Str('1'), level=2, identifier='intro-1'),
        toc_div(BulletList(
            ListItem(Plain(Link(Str('Intro 1.1'), url='#intro-1.1'))),
            ListItem(Plain(Link(Str('Intro 1.2'), url='#intro-1.2'))),
        )),
        Header(Str('Intro'), Space(), Str('1.1'), level=3, identifier='intro-1.1'),
        Header(Str('Intro'), Space(), Str('1.2'), level=3, identifier='intro-1.2'),

        Header(Str('Intro'), Space(), Str('2'), level=2, identifier='intro-2'),
        toc_div(BulletList(
            ListItem(Plain(Link(Str('Intro 2.1'), url='#intro-2.1'))),
            ListItem(Plain(Link(Str('Intro 2.2'), url='#intro-2.2'))),
        )),
        Header(Str('Intro'), Space(), Str('2.1'), level=3, identifier='intro-2.1'),
        Header(Str('Intro'), Space(), Str('2.2'), level=3, identifier='intro-2.2'),
    )


class TestTocDirective_Combined(AbstractTestTocDirective):
    SOURCE = '''
        # Introduction
        
        @toc --combined
        
        ## Intro 1
        ### Intro 1.1
        ### Intro 1.2
        ## Intro 2
        ### Intro 2.1
        ### Intro 2.2
    '''
    EXPECTED = (
        Header(Str('Introduction'), level=1),
        toc_div(BulletList(
            ListItem(Plain(Link(Str('Intro 1'), url='#intro-1')), BulletList(
                ListItem(Plain(Link(Str('Intro 1.1'), url='#intro-1.1'))),
                ListItem(Plain(Link(Str('Intro 1.2'), url='#intro-1.2'))),
            )),
            ListItem(Plain(Link(Str('Intro 2'), url='#intro-2')), BulletList(
                ListItem(Plain(Link(Str('Intro 2.1'), url='#intro-2.1'))),
                ListItem(Plain(Link(Str('Intro 2.2'), url='#intro-2.2'))),
            )),
            ListItem(Plain(Link(Str('Section 1'), url='section1/')), BulletList(
                ListItem(Plain(Link(Str('Page 1.1'), url='section1/page1.md')), BulletList(
                    ListItem(Plain(Link(Str('Paragraph'), url='section1/page1.md#paragraph'))),
                )),
                ListItem(Plain(Link(Str('Page 1.2'), url='section1/page2.md')), BulletList(
                    ListItem(Plain(Link(Str('Paragraph'), url='section1/page2.md#paragraph'))),
                )),
            )),
            ListItem(Plain(Link(Str('Section 2'), url='section2/')), BulletList(
                ListItem(Plain(Link(Str('Page 2.1'), url='section2/page1.md')), BulletList(
                    ListItem(Plain(Link(Str('Paragraph'), url='section2/page1.md#paragraph'))),
                )),
                ListItem(Plain(Link(Str('Page 2.2'), url='section2/page2.md')), BulletList(
                    ListItem(Plain(Link(Str('Paragraph'), url='section2/page2.md#paragraph'))),
                )),
            )),
            ListItem(Plain(Link(Str('Section 3'), url='section3/'))),
        )),
        Header(Str('Intro'), Space(), Str('1'), level=2, identifier='intro-1'),
        Header(Str('Intro'), Space(), Str('1.1'), level=3, identifier='intro-1.1'),
        Header(Str('Intro'), Space(), Str('1.2'), level=3, identifier='intro-1.2'),
        Header(Str('Intro'), Space(), Str('2'), level=2, identifier='intro-2'),
        Header(Str('Intro'), Space(), Str('2.1'), level=3, identifier='intro-2.1'),
        Header(Str('Intro'), Space(), Str('2.2'), level=3, identifier='intro-2.2'),
    )


class TestTocDirective_Combined_Subheader(AbstractTestTocDirective):
    SOURCE = '''
        # Introduction
        
        ## Intro 1
        
        @toc --combined
        
        ### Intro 1.1
        ### Intro 1.2
        ## Intro 2
        ### Intro 2.1
        ### Intro 2.2
    '''

    EXPECTED_ISSUES = (
        "Cannot use '@toc --combined' under a sub-header.",
    )

    test_doc = None


del SinglePageProjectTest, AbstractTestTocDirective

if __name__ == '__main__':
    unittest.main()

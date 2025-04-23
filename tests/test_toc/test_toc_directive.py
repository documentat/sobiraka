from unittest import main

from panflute import BulletList, Div, Element, Link, ListItem, Plain, Str

from abstracttests.projecttestcase import ProjectTestCase
from helpers import FakeBuilder
from helpers.fakeproject import FakeProject, FakeVolume
from sobiraka.models import Project, Status
from sobiraka.runtime import RT


class AbstractTestTocDirective(ProjectTestCase[FakeBuilder]):
    REQUIRE = Status.NUMERATE

    directive: str
    expected: Element

    def _init_project(self) -> Project:
        return FakeProject({
            'src': FakeVolume({
                'index.md': self.directive,
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

    async def test_toc_directive(self):
        volume = self.project.get_volume()
        actual = RT[volume.root_page].doc.content[0]
        self.assertEqual(self.expected, actual)


class TestTocDirective_Default(AbstractTestTocDirective):
    directive = '@toc'
    expected = Div(BulletList(
        ListItem(Plain(Link(Str('Section 1'), url='section1/')), BulletList(
            ListItem(Plain(Link(Str('Page 1.1'), url='section1/page1.md'))),
            ListItem(Plain(Link(Str('Page 1.2'), url='section1/page2.md'))),
        )),
        ListItem(Plain(Link(Str('Section 2'), url='section2/')), BulletList(
            ListItem(Plain(Link(Str('Page 2.1'), url='section2/page1.md'))),
            ListItem(Plain(Link(Str('Page 2.2'), url='section2/page2.md'))),
        )),
        ListItem(Plain(Link(Str('Section 3'), url='section3/'))),
    ), classes=['toc'])


class TestTocDirective_Combined(AbstractTestTocDirective):
    directive = '@toc --combined'
    expected = Div(BulletList(
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
    ), classes=['toc'])


class TestTocDirective_Depth(AbstractTestTocDirective):
    directive = '@toc --depth=1'
    expected = Div(BulletList(
        ListItem(Plain(Link(Str('Section 1'), url='section1/'))),
        ListItem(Plain(Link(Str('Section 2'), url='section2/'))),
        ListItem(Plain(Link(Str('Section 3'), url='section3/'))),
    ), classes=['toc'])


del ProjectTestCase, AbstractTestTocDirective

if __name__ == '__main__':
    main()

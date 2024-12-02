from unittest import main
from unittest.mock import Mock

from panflute import BulletList, Div, Element, Link, ListItem, Plain, Str

from abstracttests.projecttestcase import ProjectTestCase
from helpers import FakeBuilder
from sobiraka.models import FileSystem, Page, PageStatus, Project, Volume
from sobiraka.runtime import RT
from sobiraka.utils import RelativePath


class AbstractTestTocDirective(ProjectTestCase[FakeBuilder]):
    REQUIRE = PageStatus.PROCESS3

    directive: str
    expected: Element

    def _init_project(self) -> Project:
        return Project(Mock(FileSystem), {
            RelativePath('src'): Volume({
                RelativePath(): Page(self.directive),
                RelativePath('section1'): Page('# Section 1'),
                RelativePath('section1/page1.md'): Page('# Page 1.1\n## Paragraph'),
                RelativePath('section1/page2.md'): Page('# Page 1.2\n## Paragraph'),
                RelativePath('section2'): Page('# Section 2'),
                RelativePath('section2/page1.md'): Page('# Page 2.1\n## Paragraph'),
                RelativePath('section2/page2.md'): Page('# Page 2.2\n## Paragraph'),
            }),
        })

    async def test_toc_directive(self):
        volume = self.project.get_volume()
        actual = RT[volume.root_page].doc.content[0]
        self.assertEqual(self.expected, actual)


class TestTocDirective_Default(AbstractTestTocDirective):
    directive = '@toc'
    expected = Div(BulletList(
        ListItem(Plain(Link(Str('Section 1'), url='section1')), BulletList(
            ListItem(Plain(Link(Str('Page 1.1'), url='section1/page1.md'))),
            ListItem(Plain(Link(Str('Page 1.2'), url='section1/page2.md'))),
        )),
        ListItem(Plain(Link(Str('Section 2'), url='section2')), BulletList(
            ListItem(Plain(Link(Str('Page 2.1'), url='section2/page1.md'))),
            ListItem(Plain(Link(Str('Page 2.2'), url='section2/page2.md'))),
        )),
    ), classes=['toc'])


class TestTocDirective_Combine(AbstractTestTocDirective):
    directive = '@toc --combine'
    expected = Div(BulletList(
        ListItem(Plain(Link(Str('Section 1'), url='section1')), BulletList(
            ListItem(Plain(Link(Str('Page 1.1'), url='section1/page1.md')), BulletList(
                ListItem(Plain(Link(Str('Paragraph'), url='section1/page1.md#paragraph'))),
            )),
            ListItem(Plain(Link(Str('Page 1.2'), url='section1/page2.md')), BulletList(
                ListItem(Plain(Link(Str('Paragraph'), url='section1/page2.md#paragraph'))),
            )),
        )),
        ListItem(Plain(Link(Str('Section 2'), url='section2')), BulletList(
            ListItem(Plain(Link(Str('Page 2.1'), url='section2/page1.md')), BulletList(
                ListItem(Plain(Link(Str('Paragraph'), url='section2/page1.md#paragraph'))),
            )),
            ListItem(Plain(Link(Str('Page 2.2'), url='section2/page2.md')), BulletList(
                ListItem(Plain(Link(Str('Paragraph'), url='section2/page2.md#paragraph'))),
            )),
        )),
    ), classes=['toc'])


class TestTocDirective_Depth(AbstractTestTocDirective):
    directive = '@toc --depth=1'
    expected = Div(BulletList(
        ListItem(Plain(Link(Str('Section 1'), url='section1'))),
        ListItem(Plain(Link(Str('Section 2'), url='section2'))),
    ), classes=['toc'])


del ProjectTestCase, AbstractTestTocDirective

if __name__ == '__main__':
    main()

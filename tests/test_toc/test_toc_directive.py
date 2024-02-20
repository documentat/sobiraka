from pathlib import Path
from unittest import main
from unittest.mock import Mock

from panflute import BulletList, Element, Link, ListItem, Plain, Space, Str

from abstracttests.projecttestcase import ProjectTestCase
from helpers.fakeprocessor import FakeProcessor
from sobiraka.models import FileSystem, Page, Project, Volume
from sobiraka.models.config import Config, Config_Content
from sobiraka.runtime import RT


class AbstractTestTocDirective(ProjectTestCase[FakeProcessor]):
    numeration: bool = False
    directive: str
    expected: Element

    def _init_project(self) -> Project:
        return Project(Mock(FileSystem), {
            Path('src'): Volume(
                Config(
                    content=Config_Content(
                        numeration=self.numeration,
                    ),
                ),
                {
                    Path(): Page(self.directive),
                    Path('section1'): Page('# Section 1'),
                    Path('section1/page1.md'): Page('# Page 1.1\n## Paragraph'),
                    Path('section1/page2.md'): Page('# Page 1.2\n## Paragraph'),
                    Path('section2'): Page('# Section 2'),
                    Path('section2/page1.md'): Page('# Page 2.1\n## Paragraph'),
                    Path('section2/page2.md'): Page('# Page 2.2\n## Paragraph'),
                },
            ),
        })

    async def test_toc_directive(self):
        # self.assertEqual(self.toc_mock.)
        volume = self.project.get_volume()
        await self.processor.process3(volume)

        actual = RT[volume.root_page].doc.content[0]
        self.assertEqual(self.expected, actual)


class TestTocDirective_Default(AbstractTestTocDirective):
    directive = '@toc'
    expected = BulletList(
        ListItem(Plain(Link(Str('Section 1'), url='section1')), BulletList(
            ListItem(Plain(Link(Str('Page 1.1'), url='section1/page1.md'))),
            ListItem(Plain(Link(Str('Page 1.2'), url='section1/page2.md'))),
        )),
        ListItem(Plain(Link(Str('Section 2'), url='section2')), BulletList(
            ListItem(Plain(Link(Str('Page 2.1'), url='section2/page1.md'))),
            ListItem(Plain(Link(Str('Page 2.2'), url='section2/page2.md'))),
        )),
    )


class TestTocDirective_Combine(AbstractTestTocDirective):
    directive = '@toc --combine'
    expected = BulletList(
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
    )


class TestTocDirective_Depth(AbstractTestTocDirective):
    directive = '@toc --depth=1'
    expected = BulletList(
        ListItem(Plain(Link(Str('Section 1'), url='section1'))),
        ListItem(Plain(Link(Str('Section 2'), url='section2'))),
    )


class TestTocDirective_Numeration(AbstractTestTocDirective):
    numeration = True
    directive = '@toc'
    expected = BulletList(
        ListItem(Plain(Str('1.'), Space(), Link(Str('Section 1'), url='section1')), BulletList(
            ListItem(Plain(Str('1.1.'), Space(), Link(Str('Page 1.1'), url='section1/page1.md'))),
            ListItem(Plain(Str('1.2.'), Space(), Link(Str('Page 1.2'), url='section1/page2.md'))),
        )),
        ListItem(Plain(Str('2.'), Space(), Link(Str('Section 2'), url='section2')), BulletList(
            ListItem(Plain(Str('2.1.'), Space(), Link(Str('Page 2.1'), url='section2/page1.md'))),
            ListItem(Plain(Str('2.2.'), Space(), Link(Str('Page 2.2'), url='section2/page2.md'))),
        )),
    )


class TestTocDirective_Numeration_Format(AbstractTestTocDirective):
    numeration = True
    directive = '@toc --format="({})"'
    expected = BulletList(
        ListItem(Plain(Str('(1)'), Space(), Link(Str('Section 1'), url='section1')), BulletList(
            ListItem(Plain(Str('(1.1)'), Space(), Link(Str('Page 1.1'), url='section1/page1.md'))),
            ListItem(Plain(Str('(1.2)'), Space(), Link(Str('Page 1.2'), url='section1/page2.md'))),
        )),
        ListItem(Plain(Str('(2)'), Space(), Link(Str('Section 2'), url='section2')), BulletList(
            ListItem(Plain(Str('(2.1)'), Space(), Link(Str('Page 2.1'), url='section2/page1.md'))),
            ListItem(Plain(Str('(2.2)'), Space(), Link(Str('Page 2.2'), url='section2/page2.md'))),
        )),
    )


del ProjectTestCase, AbstractTestTocDirective

if __name__ == '__main__':
    main()

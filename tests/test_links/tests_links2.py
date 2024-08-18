from unittest import main
from unittest.mock import Mock

from panflute import Link

from abstracttests.projecttestcase import ProjectTestCase
from sobiraka.models import FileSystem, Page, PageHref, Project, Volume
from sobiraka.runtime import RT
from sobiraka.utils import RelativePath


class TestLinks2(ProjectTestCase):
    def _init_project(self) -> Project:
        fs = Mock(FileSystem)
        return Project(fs, {
            RelativePath('A'): Volume(None, 'A', {
                RelativePath() / 'page.md': Page(),
                RelativePath() / 'section1' / 'page.md': Page(),
                RelativePath() / 'section1' / 'subsection1' / 'page.md': Page(),  # <-- we will start here
                RelativePath() / 'section1' / 'subsection1' / 'sibling.md': Page(),
                RelativePath() / 'section1' / 'subsection1' / 'subsubsection1' / 'page.md': Page(),
                RelativePath() / 'section1' / 'subsection2' / 'page.md': Page(),
                RelativePath() / 'section2' / 'page.md': Page(),
            }),
            RelativePath('B'): Volume(None, 'B', {
                RelativePath() / 'page.md': Page(),
            })
        })

    async def test_links(self):
        page = self.project.pages_by_path[RelativePath('A/section1/subsection1/page.md')]
        data: dict[str, RelativePath] = {
            '/': RelativePath('A'),
            '/page.md': RelativePath('A/page.md'),
            '/section1': RelativePath('A/section1'),
            '/section1/page.md': RelativePath('A/section1/page.md'),
            '/section1/subsection1': RelativePath('A/section1/subsection1'),
            '/section1/subsection1/page.md': RelativePath('A/section1/subsection1/page.md'),
            '/section1/subsection1/sibling.md': RelativePath('A/section1/subsection1/sibling.md'),
            '/section1/subsection1/subsubsection1': RelativePath('A/section1/subsection1/subsubsection1'),
            '/section1/subsection1/subsubsection1/page.md': RelativePath('A/section1/subsection1/subsubsection1/page.md'),
            '/section1/subsection2': RelativePath('A/section1/subsection2'),
            '/section1/subsection2/page.md': RelativePath('A/section1/subsection2/page.md'),
            '/section2': RelativePath('A/section2'),
            '/section2/page.md': RelativePath('A/section2/page.md'),
            '../..': RelativePath('A'),
            '../../page.md': RelativePath('A/page.md'),
            '..': RelativePath('A/section1'),
            '../page.md': RelativePath('A/section1/page.md'),
            '.': RelativePath('A/section1/subsection1'),
            '': RelativePath('A/section1/subsection1/page.md'),
            'page.md': RelativePath('A/section1/subsection1/page.md'),
            'sibling.md': RelativePath('A/section1/subsection1/sibling.md'),
            'subsubsection1': RelativePath('A/section1/subsection1/subsubsection1'),
            'subsubsection1/page.md': RelativePath('A/section1/subsection1/subsubsection1/page.md'),
            '../subsection2': RelativePath('A/section1/subsection2'),
            '../subsection2/page.md': RelativePath('A/section1/subsection2/page.md'),
            '../../section2': RelativePath('A/section2'),
            '../../section2/page.md': RelativePath('A/section2/page.md'),
            '$A/page.md': RelativePath('A/page.md'),
            '$B/page.md': RelativePath('B/page.md'),
        }
        for target_text, expected_path in data.items():
            with self.subTest(target=target_text):
                previous_links_count = len(RT[page].links)
                await self.processor._process_internal_link(Link(), target_text, page)
                self.assertEqual(previous_links_count + 1, len(RT[page].links))

                href = RT[page].links[-1]
                self.assertIsInstance(href, PageHref)
                self.assertEqual(expected_path, href.target.path_in_project)
                self.assertEqual(None, href.anchor)


del ProjectTestCase

if __name__ == '__main__':
    main()

from unittest import main

from abstracttests.abstracttestwithrt import AbstractTestWithRtPages
from abstracttests.projecttestcase import ProjectTestCase
from helpers import FakeBuilder
from helpers.fakeproject import FakeProject, FakeVolume
from sobiraka.models import PageHref, Status
from sobiraka.models.config import Config, Config_Paths
from sobiraka.runtime import RT
from sobiraka.utils import RelativePath


class TestLinks2(AbstractTestWithRtPages):
    def make_project(self) -> FakeProject:
        config_a = Config(paths=Config_Paths(root=RelativePath('A')))
        config_b = Config(paths=Config_Paths(root=RelativePath('B')))
        return FakeProject({
            'A': FakeVolume(config_a, {
                'page.md': '',
                'section1/page.md': '',
                'section1/subsection1/page.md': '',  # <-- we will start here
                'section1/subsection1/sibling.md': '',
                'section1/subsection1/subsubsection1/page.md': '',
                'section1/subsection2/page.md': '',
                'section2/page.md': '',
            }),
            'B': FakeVolume(config_b, {
                'page.md': '',
            })
        })

    async def test_links(self):
        # pylint: disable=line-too-long
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
                RT.init_context_vars()

                project = self.make_project()
                project.fs.pseudofiles[RelativePath('A/section1/subsection1/page.md')] = f'[Link]({target_text})'

                builder = FakeBuilder(project)
                builder.init_waiter(Status.REFERENCE)
                await builder.waiter.wait_all()

                page = project.volumes[0].get_page_by_location('/section1/subsection1/page')
                href, = RT[page].links

                self.assertIsInstance(href, PageHref)
                self.assertEqual(expected_path, href.target.source.path_in_project)
                self.assertEqual(None, href.anchor)


del ProjectTestCase

if __name__ == '__main__':
    main()

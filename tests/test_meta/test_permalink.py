import unittest

from abstracttests.abstracttestwithrt import AbstractTestWithRtTmp
from abstracttests.projecttestcase import ProjectTestCase
from helpers.fakeproject import FakeProject, FakeVolume
from sobiraka.models import Project, Status
from sobiraka.models.config import Config, Config_Paths, Config_Theme, Config_Web
from sobiraka.processing.web import WebBuilder
from sobiraka.runtime import RT
from sobiraka.utils import RelativePath


class TestPermalink(ProjectTestCase[WebBuilder], AbstractTestWithRtTmp):
    REQUIRE = Status.PROCESS4

    def _init_project(self) -> Project:
        config = Config(
            paths=Config_Paths(root=RelativePath('src')),
            web=Config_Web(theme=Config_Theme.from_name('raw'))
        )
        return FakeProject({
            'src': FakeVolume(config, {
                'A': '''
                    ---
                    permalink: /AAA
                    ---
                    # A
                    See also: [](B).
                    ''',
                'B': '''
                    ---
                    permalink: /BBB/
                    ---
                    # B
                    See also: [](A).
                    ''',
            }),
        })

    def _init_builder(self):
        return WebBuilder(self.project, RT.TMP)

    def test_html(self):
        data = {
            '/A': '<h1 data-local-level="1" data-global-level="2" data-number="">A</h1>\n'
                  '<p>See also: <a href="BBB/index.html">B</a>.</p>',
            '/B': '<h1 data-local-level="1" data-global-level="2" data-number="">B</h1>\n'
                  '<p>See also: <a href="../AAA.html">A</a>.</p>',
        }

        for location, expected in data.items():
            with self.subTest(location):
                page = self.project.get_volume().get_page_by_location(location)
                actual = RT[page].bytes.decode('utf-8')
                self.assertEqual(expected, actual)


if __name__ == '__main__':
    unittest.main()

from importlib.resources import files
from tempfile import TemporaryDirectory
from unittest import main

from abstracttests.projecttestcase import ProjectTestCase
from helpers.fakeproject import FakeProject, FakeVolume
from sobiraka.models import Project, Status
from sobiraka.models.config import Config, Config_Paths, Config_Web
from sobiraka.processing.web import WebBuilder
from sobiraka.utils import AbsolutePath, RelativePath


class TestHtmlImages(ProjectTestCase[WebBuilder]):
    REQUIRE = Status.PROCESS4

    def _init_builder(self) -> WebBuilder:
        # pylint: disable=consider-using-with
        output = self.enterContext(TemporaryDirectory(prefix='sobiraka-test-'))
        return WebBuilder(self.project, AbsolutePath(output))

    def _init_project(self) -> Project:
        config = Config(
            paths=Config_Paths(
                root=RelativePath('src'),
                resources=RelativePath('img_src'),
            ),
            web=Config_Web(
                theme=AbsolutePath(files('sobiraka')) / 'files' / 'themes' / 'raw',
                resources_prefix='img_dst',
            )
        )

        project = FakeProject({
            'src': FakeVolume(config, {
                'absolute.md': '![](/absolute.png)',
                'relative.md': '![](../img_src/relative.png)',
            })
        })
        project.fs.add_files({
            'img_src/absolute.png': 'absolute',
            'img_src/relative.png': 'relative',
        })
        return project

    def test_images(self):
        for name in ('absolute', 'relative'):
            with self.subTest(name):
                actual = (self.builder.output / 'img_dst' / f'{name}.png').read_bytes()
                self.assertEqual(name.encode(), actual)

    def test_html(self):
        for name in ('absolute', 'relative'):
            with self.subTest(name):
                expected = f'<img src="../img_dst/{name}.png" />'
                actual = (self.builder.output / 'src' / f'{name}.html').read_text()
                self.assertIn(expected, actual)


del ProjectTestCase

if __name__ == '__main__':
    main()

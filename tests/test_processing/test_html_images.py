from tempfile import TemporaryDirectory
from textwrap import dedent
from unittest import main

from abstracttests.projecttestcase import ProjectTestCase
from helpers import FakeFileSystem
from sobiraka.models import Project
from sobiraka.models.load import load_project_from_str
from sobiraka.processing.web import WebBuilder
from sobiraka.utils import AbsolutePath


class TestHtmlImages(ProjectTestCase[WebBuilder]):
    def _init_project(self) -> Project:
        manifest = dedent("""
        paths:
            root: src
            resources: img_src
        web:
            theme: raw
            resources_prefix: img_dst
        """)

        fs = FakeFileSystem()
        fs['img_src/absolute.png'] = b'absolute'
        fs['img_src/relative.png'] = b'relative'
        fs['src/absolute.md'] = '![](/absolute.png)'
        fs['src/relative.md'] = '![](../img_src/relative.png)'

        return load_project_from_str(manifest, fs=fs)

    def _init_builder(self) -> WebBuilder:
        output = self.enterContext(TemporaryDirectory(prefix='sobiraka-test-'))
        return WebBuilder(self.project, AbsolutePath(output))

    async def asyncSetUp(self):
        await super().asyncSetUp()
        await self.builder.run()

    def test_images(self):
        for name in ('absolute', 'relative'):
            with self.subTest(name):
                actual = (self.builder.output / 'img_dst' / f'{name}.png').read_bytes()
                self.assertEqual(name.encode(), actual)

    def test_html(self):
        for name in ('absolute', 'relative'):
            with self.subTest(name):
                expected = f'<img src="img_dst/{name}.png" />'
                actual = (self.builder.output / f'{name}.html').read_text()
                self.assertIn(expected, actual)


del ProjectTestCase

if __name__ == '__main__':
    main()

from pathlib import Path
from tempfile import TemporaryDirectory
from textwrap import dedent
from unittest import main

from abstracttests.projecttestcase import ProjectTestCase
from helpers.fakefilesystem import FakeFileSystem
from sobiraka.models import Project
from sobiraka.models.load import load_project_from_str
from sobiraka.processing import HtmlBuilder


class TestHtmlImages(ProjectTestCase[HtmlBuilder]):
    def _init_project(self) -> Project:
        manifest = dedent("""
        paths:
            root: src
            resources: img_src
        html:
            resources_prefix: img_dst
        """)

        fs = FakeFileSystem()
        fs['img_src/absolute.png'] = b'absolute'
        fs['img_src/relative.png'] = b'relative'
        fs['src/absolute.md'] = '![](/absolute.png)'
        fs['src/relative.md'] = '![](../img_src/relative.png)'

        return load_project_from_str(manifest, fs=fs)

    def _init_processor(self) -> HtmlBuilder:
        output = self.enterContext(TemporaryDirectory(prefix='sobiraka-test-'))
        return HtmlBuilder(self.project, Path(output))

    async def asyncSetUp(self):
        await super().asyncSetUp()
        await self.processor.run()

    def test_images(self):
        for name in ('absolute', 'relative'):
            with self.subTest(name):
                actual = (self.processor.output / 'img_dst' / f'{name}.png').read_bytes()
                self.assertEqual(name.encode(), actual)

    def test_html(self):
        for name in ('absolute', 'relative'):
            with self.subTest(name):
                expected = f'<img src="img_dst/{name}.png" />'
                actual = (self.processor.output / f'{name}.html').read_text()
                self.assertIn(expected, actual)


del ProjectTestCase

if __name__ == '__main__':
    main()

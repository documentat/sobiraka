from pathlib import Path
from textwrap import dedent
from unittest import main, TestCase

from sobiraka.models import Volume, Project, Version
from sobiraka.models.config import Config_Paths
from testutils import FakePage


class TestMeta(TestCase):
    def setUp(self) -> None:
        self.project = Project(
            base=Path('/fake-project'),
            volumes=(
                Volume(paths=Config_Paths(root=Path())),
            ))

    def _page(self, meta_text: str) -> FakePage:
        return FakePage(self.project.volumes[0], Path('/fake-project/page.md'), _meta_text=meta_text)

    def test_no_meta(self):
        page = self._page('')
        self.assertDictEqual({}, page.meta)

    def test_empty_meta(self):
        page = self._page('\n')
        self.assertDictEqual({}, page.meta)

    def test_unknown_variables(self):
        page = self._page(dedent('''
            foo: 1
            bar: X
        '''))
        self.assertDictEqual({'foo': 1, 'bar': 'X'}, page.meta)

    def test_version(self):
        page = self._page('version: 12.3')
        with self.subTest('access raw value'):
            self.assertDictEqual({'version': 12.3}, page.meta)
        with self.subTest('access object'):
            self.assertEqual(Version(12,3), page.meta.version)


if __name__ == '__main__':
    main()

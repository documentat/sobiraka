from pathlib import Path
from tempfile import TemporaryDirectory
from textwrap import dedent
from unittest import TestCase, main
from unittest.mock import Mock

from sobiraka.models import Page, PageMeta, Version, Volume


class TestInitPage(TestCase):

    def test_with_volume_path(self):
        with TemporaryDirectory(prefix='sobiraka-test-') as tmpdir:
            volume_root = Path(tmpdir)

            page_path = volume_root / 'page.md'
            page_path.write_text(dedent('''
            ---
            version: 1.23
            ---
            Hello, world!
            ''').strip())

            volume = Mock(Volume, root=volume_root)
            page = Page(volume, page_path)

            with self.subTest('volume'):
                self.assertIs(volume, page.volume)
            with self.subTest('path'):
                self.assertEqual(page_path, page.absolute_path)
            with self.subTest('meta'):
                self.assertIsInstance(page.meta, PageMeta)
                self.assertEqual(Version(1, 23), page.meta.version)
            with self.subTest('text'):
                self.assertEqual('Hello, world!', page.text)

    def test_with_path(self):
        path = Path('/example.md')
        page = Page(path)

        with self.subTest('volume'):
            self.assertIsNone(page.volume)
        with self.subTest('path'):
            self.assertEqual(path, page.path_in_volume)
        with self.subTest('meta'):
            with self.assertRaises(AttributeError):
                _ = page.meta
        with self.subTest('text'):
            with self.assertRaises(AttributeError):
                _ = page.text

    def test_with_meta_text(self):
        page = Page(PageMeta(version=Version(1, 23)), 'Hello, world!')

        with self.subTest('volume'):
            self.assertIsNone(page.volume)
        with self.subTest('path'):
            self.assertIsNone(page.path_in_volume)
        with self.subTest('meta'):
            self.assertIsInstance(page.meta, PageMeta)
            self.assertEqual(Version(1, 23), page.meta.version)
        with self.subTest('text'):
            self.assertEqual('Hello, world!', page.text)

    def test_with_text(self):
        page = Page(dedent('''
        ---
        version: 1.23
        ---
        Hello, world!
        ''').strip())

        with self.subTest('volume'):
            self.assertIsNone(page.volume)
        with self.subTest('path'):
            self.assertIsNone(page.path_in_volume)
        with self.subTest('meta'):
            self.assertIsInstance(page.meta, PageMeta)
            self.assertEqual(Version(1, 23), page.meta.version)
        with self.subTest('text'):
            self.assertEqual('Hello, world!', page.text)

    def test_with_nothing(self):
        page = Page()

        with self.subTest('volume'):
            self.assertIsNone(page.volume)
        with self.subTest('path'):
            self.assertIsNone(page.path_in_volume)
        with self.subTest('meta'):
            self.assertEqual(PageMeta(), page.meta)
        with self.subTest('text'):
            self.assertEqual('', page.text)


if __name__ == '__main__':
    main()

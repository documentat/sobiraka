from unittest import TestCase, main

from sobiraka.models import Page, Version


class TestMeta(TestCase):
    def test_no_meta(self):
        page = Page('Hello, world!')
        self.assertIsNone(page.meta.version)

    def test_empty_meta(self):
        page = Page('---\n---\nHello, world!')
        self.assertIsNone(page.meta.version)

    def test_version(self):
        page = Page('---\nversion: 12.3\n---\nHello, world!')
        self.assertEqual(Version(12, 3), page.meta.version)


if __name__ == '__main__':
    main()

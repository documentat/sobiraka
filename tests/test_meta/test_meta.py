from unittest import TestCase, main

from sobiraka.models import Page, Version


class TestMeta(TestCase):
    def test_no_meta(self):
        page = Page('Hello, world!')
        self.assertIsNone(page.meta.version)

    def test_empty_meta(self):
        page = Page('---\n---\nHello, world!')
        self.assertIsNone(page.meta.version)


class TestMeta_Version(TestCase):
    def test_version_12_0(self):
        page = Page('---\nversion: 12\n---\nHello, world!')
        self.assertEqual(Version(12, 0), page.meta.version)

    def test_version_12_3(self):
        page = Page('---\nversion: 12.3\n---\nHello, world!')
        self.assertEqual(Version(12, 3), page.meta.version)


class TestMeta_Title(TestCase):
    def test_title(self):
        page = Page('---\ntitle: Hello\n---\nHello, world!')
        self.assertEqual('Hello', page.meta.title)


if __name__ == '__main__':
    main()

from unittest import main

from abstracttests.singlepageprojecttest import SinglePageProjectTest
from sobiraka.models import Version


class TestMeta_No(SinglePageProjectTest):
    SOURCE = 'Hello, world!'

    def test_meta(self):
        self.assertIsNone(self.page.meta.version)


class TestMeta_Empty(SinglePageProjectTest):
    SOURCE = '---\n---\nHello, world!'

    def test_meta(self):
        self.assertIsNone(self.page.meta.version)


class TestMeta_Version_12_0(SinglePageProjectTest):
    SOURCE = '---\nversion: 12\n---\nHello, world!'

    def test_meta(self):
        self.assertEqual(Version(12, 0), self.page.meta.version)


class TestMeta_Version_12_3(SinglePageProjectTest):
    SOURCE = '---\nversion: 12.3\n---\nHello, world!'

    def test_meta(self):
        self.assertEqual(Version(12, 3), self.page.meta.version)


class TestMeta_Title(SinglePageProjectTest):
    SOURCE = '---\ntitle: Hello\n---\nHello, world!'

    def test_meta(self):
        self.assertEqual('Hello', self.page.meta.title)


class TestMeta_LongSeparators(SinglePageProjectTest):
    SOURCE = '----------\ntitle: Hello\n------\nHello, world!'

    def test_meta(self):
        self.assertEqual('Hello', self.page.meta.title)


del SinglePageProjectTest

if __name__ == '__main__':
    main()

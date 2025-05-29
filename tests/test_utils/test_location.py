import unittest
from unittest import TestCase

from sobiraka.utils import Location, RelativePath


class TestLocation(TestCase):

    def test_level(self):
        for text, expected in {
            '/': 1,
            '/haha': 2,
            '/haha/': 2,
            '/haha/hoho': 3,
            '/haha/hoho/': 3,
            '/haha/hoho/hehe': 4,
            '/haha/hoho/hehe/': 4,
        }.items():
            with self.subTest(text):
                self.assertEqual(expected, Location(text).level)

    def test_is_dir(self):
        for text, expected in {
            '/': True,
            '/haha': False,
            '/haha/': True,
            '/haha/hoho': False,
            '/haha/hoho/': True,
            '/haha/hoho/hehe': False,
            '/haha/hoho/hehe/': True,
        }.items():
            with self.subTest(text):
                self.assertEqual(expected, Location(text).is_dir)

    def test_parent(self):
        for text, expected in {
            '/': None,
            '/haha': Location('/'),
            '/haha/': Location('/'),
            '/haha/hoho': Location('/haha/'),
            '/haha/hoho/': Location('/haha/'),
            '/haha/hoho/hehe': Location('/haha/hoho/'),
            '/haha/hoho/hehe/': Location('/haha/hoho/'),
        }.items():
            with self.subTest(text):
                self.assertEqual(expected, Location(text).parent)

    def test_name(self):
        for text, expected in {
            '/': None,
            '/haha': 'haha',
            '/haha/': 'haha',
            '/haha/hoho': 'hoho',
            '/haha/hoho/': 'hoho',
            '/haha/hoho/hehe': 'hehe',
            '/haha/hoho/hehe/': 'hehe',
        }.items():
            with self.subTest(text):
                self.assertEqual(expected, Location(text).name)

    def test_as_path(self):
        for text, expected in {
            '/': RelativePath(''),
            '/haha': RelativePath('haha'),
            '/haha/': RelativePath('haha/'),
            '/haha/hoho': RelativePath('haha/hoho'),
            '/haha/hoho/': RelativePath('haha/hoho/'),
            '/haha/hoho/hehe': RelativePath('haha/hoho/hehe'),
            '/haha/hoho/hehe/': RelativePath('haha/hoho/hehe/'),
        }.items():
            with self.subTest(text):
                self.assertEqual(expected, Location(text).as_path())

    def test_as_relative_path_str(self):
        for (start, text), expected in {
            (None, '/'): 'index.html',
            ('/', '/'): '',
            ('/', '/haha'): 'haha.html',
            ('/', '/haha/'): 'haha/index.html',

            ('/haha', '/'): 'index.html',
            ('/haha', '/haha'): '',
            ('/haha', '/other/dir/'): 'other/dir/index.html',

            ('/haha/', '/'): '../index.html',
            ('/haha/', '/haha/'): '',
            ('/haha/', '/haha/lol'): 'lol.html',
            ('/haha/', '/other/dir/'): '../other/dir/index.html',

            ('/haha/hoho/', '/'): '../../index.html',
            ('/haha/hoho/', '/haha/hoho/'): '',
            ('/haha/hoho/', '/haha/'): '../index.html',
            ('/haha/hoho/', '/haha/hoho/lol'): 'lol.html',
            ('/haha/hoho/', '/other/dir/'): '../../other/dir/index.html',

            ('/haha/hoho/lol', '/haha/'): '../index.html',
            ('/haha/hoho/lol', '/haha/hoho/'): 'index.html',
            ('/haha/hoho/lol', '/haha/hoho/lol'): '',
        }.items():
            with self.subTest(f'{start} → {text}'):
                actual = Location(text).as_relative_path_str(start=start and Location(start),
                                                             suffix='.html',
                                                             index_file_name='index.html')
                self.assertEqual(expected, actual)


if __name__ == '__main__':
    unittest.main()

from pathlib import Path, PurePath
from typing import Callable, Type
from unittest import TestCase

from sobiraka.utils import AbsolutePath, PathGoesOutsideStartDirectory, RelativePath, WrongPathType, \
    absolute_or_relative


class TestAbsolutePath(TestCase):

    def test_init(self):
        data = {
            '': AbsolutePath(Path()),
            '.': AbsolutePath(Path()),
            './': AbsolutePath(Path()),
            'foo/bar': AbsolutePath(Path() / 'foo' / 'bar'),
            '../foo/bar': AbsolutePath(Path()).parent / 'foo' / 'bar',
            '/foo': AbsolutePath('/foo'),
        }
        for path_str, expected in data.items():
            with self.subTest(path_str):
                actual = AbsolutePath(path_str)
                self.assertEqual(expected, actual)


class TestRelativePath(TestCase):

    def test_init(self):
        data = {
            '': '.',
            '.': '.',
            './': '.',
            'foo/bar': 'foo/bar',
            '../foo/bar': '../foo/bar',
            '/foo': WrongPathType,
        }
        for path_str, expected in data.items():
            with self.subTest(path_str):
                if isinstance(expected, str):
                    expected = RelativePath(expected)
                    actual = RelativePath(path_str)
                    self.assertEqual(expected, actual)
                else:
                    with self.assertRaises(expected):
                        _ = RelativePath(path_str)

    ############################################################################

    def test_truediv(self, target_type: Type | Callable = absolute_or_relative):
        source = RelativePath('foo/bar')
        data = {
            # Relative paths
            'baz': RelativePath('foo/bar/baz'),
            '..': RelativePath('foo'),
            '../..': RelativePath('.'),
            '../../..': PathGoesOutsideStartDirectory,

            # Absolute paths
            '/foo/bar': AbsolutePath('/foo/bar'),
            '/other': AbsolutePath('/other'),
            '/': AbsolutePath('/'),
        }
        for target, expected in data.items():
            with self.subTest(target):
                target = target_type(target)
                if isinstance(expected, PurePath):
                    actual = source / target
                    self.assertEqual(expected, actual)
                else:
                    with self.assertRaises(expected):
                        _ = source / target

    def test_truediv__Path(self):
        self.test_truediv(Path)

    def test_truediv__str(self):
        self.test_truediv(str)

    ############################################################################

    def test_relative_to(self, start_type: Type | Callable = absolute_or_relative):
        path = RelativePath('foo/bar')
        data = {
            'foo/bar/baz': '..',
            'foo/bas/bat': '../../bar',
            'foo/baz': '../bar',
            'foo/bar': '',
            'foo': 'bar',
            '/foo': WrongPathType,
            '/': WrongPathType,
        }
        for start, expected in data.items():
            with self.subTest(start):
                start = start_type(start)
                if isinstance(expected, str):
                    expected = RelativePath(expected)
                    actual = path.relative_to(start)
                    self.assertEqual(expected, actual)
                else:
                    with self.assertRaises(expected):
                        _ = path.relative_to(start)

    def test_relative_to__Path(self):
        self.test_relative_to(Path)

    def test_relative_to__str(self):
        self.test_relative_to(str)

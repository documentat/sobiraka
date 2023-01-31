import re
from pathlib import Path
from tempfile import TemporaryDirectory
from textwrap import dedent
from unittest import IsolatedAsyncioTestCase, main

from sobiraka.models import Book


class TestBookPaths(IsolatedAsyncioTestCase):
    maxDiff = None

    def prepare_dirs(self):
        temp_dir: str = self.enterContext(TemporaryDirectory(prefix='sobiraka-test-'))
        self.root = Path(temp_dir)
        self.manifest_path = self.root / 'book.yaml'

    async def asyncSetUp(self):
        self.root: Path
        self.manifest_path: Path
        self.path_to_root: str | None = None

        self.prepare_dirs()
        self.paths: tuple[Path, ...] = (
            self.root / 'intro.md',
            self.root / 'part1' / 'chapter1.md',
            self.root / 'part1' / 'chapter2.md',
            self.root / 'part1' / 'chapter3.md',
            self.root / 'part2' / 'chapter1.md',
            self.root / 'part2' / 'chapter2.md',
            self.root / 'part2' / 'chapter3.md',
            self.root / 'part3' / 'subdir' / 'chapter1.md',
            self.root / 'part3' / 'subdir' / 'chapter2.md',
            self.root / 'part3' / 'subdir' / 'chapter3.md',
        )
        for path in self.paths:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.touch()

    async def book_from_manifest(self, manifest_str: str) -> Book:
        manifest_str = dedent(manifest_str)
        if self.path_to_root:
            manifest_str = re.sub(r'^paths:\n', f'paths:\n  root: {self.path_to_root}\n', manifest_str, flags=re.MULTILINE)
        self.manifest_path.parent.mkdir(parents=True, exist_ok=True)
        self.manifest_path.write_text(dedent(manifest_str))
        return Book.from_manifest(self.manifest_path)

    def assertPagePaths(self, book: Book, expected_paths: tuple[Path, ...]):
        actual_paths = tuple(p.path for p in book.pages)
        self.assertSequenceEqual(expected_paths, actual_paths)

    ################################################################################

    async def test_empty(self):
        book = await self.book_from_manifest('''
            paths:
              include: []
        ''')
        self.assertEqual(book.max_level, 0)
        self.assertPagePaths(book, ())

    async def test_include_all(self):
        book = await self.book_from_manifest('''
            paths:
              include: ['**/*.md']
        ''')
        # self.assertEqual(book.max_level, 4)
        self.assertPagePaths(book, (
            self.root,
            self.root / 'intro.md',
            self.root / 'part1',
            self.root / 'part1' / 'chapter1.md',
            self.root / 'part1' / 'chapter2.md',
            self.root / 'part1' / 'chapter3.md',
            self.root / 'part2',
            self.root / 'part2' / 'chapter1.md',
            self.root / 'part2' / 'chapter2.md',
            self.root / 'part2' / 'chapter3.md',
            self.root / 'part3',
            self.root / 'part3' / 'subdir',
            self.root / 'part3' / 'subdir' / 'chapter1.md',
            self.root / 'part3' / 'subdir' / 'chapter2.md',
            self.root / 'part3' / 'subdir' / 'chapter3.md',
        ))

    async def test_include_only_top_level(self):
        book = await self.book_from_manifest('''
            paths:
              include: ['*.md']
        ''')
        self.assertEqual(book.max_level, 2)
        self.assertPagePaths(book, (
            self.root,
            self.root / 'intro.md',
        ))

    async def test_include_only_part2(self):
        book = await self.book_from_manifest('''
            paths:
              include: ['part2/*.md']
        ''')
        self.assertEqual(book.max_level, 3)
        self.assertPagePaths(book, (
            self.root,
            self.root / 'part2',
            self.root / 'part2' / 'chapter1.md',
            self.root / 'part2' / 'chapter2.md',
            self.root / 'part2' / 'chapter3.md',
        ))

    async def test_include_only_chapters3(self):
        book = await self.book_from_manifest('''
            paths:
              include: ['**/chapter3.md']
        ''')
        self.assertEqual(book.max_level, 4)
        self.assertPagePaths(book, (
            self.root,
            self.root / 'part1',
            self.root / 'part1' / 'chapter3.md',
            self.root / 'part2',
            self.root / 'part2' / 'chapter3.md',
            self.root / 'part3',
            self.root / 'part3' / 'subdir',
            self.root / 'part3' / 'subdir' / 'chapter3.md',
        ))

    async def test_include_all_except_part2(self):
        book = await self.book_from_manifest('''
            paths:
              include: ['**/*.md']
              exclude: ['**/part2/*.md']
        ''')
        self.assertEqual(book.max_level, 4)
        self.assertPagePaths(book, (
            self.root,
            self.root / 'intro.md',
            self.root / 'part1',
            self.root / 'part1' / 'chapter1.md',
            self.root / 'part1' / 'chapter2.md',
            self.root / 'part1' / 'chapter3.md',
            self.root / 'part3',
            self.root / 'part3' / 'subdir',
            self.root / 'part3' / 'subdir' / 'chapter1.md',
            self.root / 'part3' / 'subdir' / 'chapter2.md',
            self.root / 'part3' / 'subdir' / 'chapter3.md',
        ))

    async def test_include_all_except_chapters3(self):
        book = await self.book_from_manifest('''
            paths:
              include: ['**/*.md']
              exclude: ['**/chapter3.md']
        ''')
        self.assertEqual(book.max_level, 4)
        self.assertPagePaths(book, (
            self.root,
            self.root / 'intro.md',
            self.root / 'part1',
            self.root / 'part1' / 'chapter1.md',
            self.root / 'part1' / 'chapter2.md',
            self.root / 'part2',
            self.root / 'part2' / 'chapter1.md',
            self.root / 'part2' / 'chapter2.md',
            self.root / 'part3',
            self.root / 'part3' / 'subdir',
            self.root / 'part3' / 'subdir' / 'chapter1.md',
            self.root / 'part3' / 'subdir' / 'chapter2.md',
        ))


class TestBookPaths_CustomRootAbsolute(TestBookPaths):
    def prepare_dirs(self):
        super().prepare_dirs()
        temp_dir: str = self.enterContext(TemporaryDirectory(prefix='sobiraka-test-'))
        self.manifest_path = Path(temp_dir) / 'book.yaml'
        self.path_to_root = str(self.root)


class TestBookPaths_CustomRootInside(TestBookPaths):
    def prepare_dirs(self):
        super().prepare_dirs()
        self.root /= 'src'
        self.path_to_root = 'src'


class TestBookPaths_CustomRootOutside(TestBookPaths):
    def prepare_dirs(self):
        super().prepare_dirs()
        self.manifest_path = self.root / 'manifest' / 'book.yaml'
        self.path_to_root = '..'


if __name__ == '__main__':
    main()
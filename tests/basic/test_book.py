from pathlib import Path
from tempfile import TemporaryDirectory
from textwrap import dedent
from unittest import IsolatedAsyncioTestCase, main

from sobiraka.models import Book


class TestBook(IsolatedAsyncioTestCase):
    maxDiff = None

    async def asyncSetUp(self):
        temp_dir: str = self.enterContext(TemporaryDirectory(prefix='sobiraka-test-'))
        self.dir: Path = Path(temp_dir)
        self.paths: tuple[Path, ...] = (
            self.dir / 'cover.md',
            self.dir / 'intro.md',
            self.dir / 'part1' / 'chapter1.md',
            self.dir / 'part1' / 'chapter2.md',
            self.dir / 'part1' / 'chapter3.md',
            self.dir / 'part2' / 'chapter1.md',
            self.dir / 'part2' / 'chapter2.md',
            self.dir / 'part2' / 'chapter3.md',
            self.dir / 'part3' / 'subdir' / 'chapter1.md',
            self.dir / 'part3' / 'subdir' / 'chapter2.md',
            self.dir / 'part3' / 'subdir' / 'chapter3.md',
        )
        for path in self.paths:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.touch()

    async def book_from_manifest(self, manifest_str: str) -> Book:
        manifest_path = self.dir / 'book.yaml'
        manifest_path.write_text(dedent(manifest_str))
        return Book.from_manifest(manifest_path)

    def assertPagePaths(self, book: Book, expected_paths: tuple[Path, ...]):
        actual_paths = tuple(p.path for p in book.pages)
        self.assertSequenceEqual(expected_paths, actual_paths)

    ################################################################################

    async def test_empty(self):
        book = await self.book_from_manifest('''
            title: Example book
            paths:
              include: []
        ''')
        self.assertEqual(book.title, 'Example book')
        self.assertEqual(book.max_level, 0)
        self.assertPagePaths(book, ())

    async def test_empty_with_auto_title(self):
        book = await self.book_from_manifest('''
            paths:
                include: []
        ''')
        self.assertEqual(book.title, self.dir.name)
        self.assertEqual(book.max_level, 0)
        self.assertPagePaths(book, ())

    async def test_include_all_files(self):
        book = await self.book_from_manifest('''
            title: Example book
            paths:
              include: ['**/*.md']
        ''')
        self.assertEqual(book.title, 'Example book')
        self.assertEqual(book.max_level, 4)
        self.assertPagePaths(book, (
            self.dir,
            self.dir / 'cover.md',
            self.dir / 'intro.md',
            self.dir / 'part1',
            self.dir / 'part1' / 'chapter1.md',
            self.dir / 'part1' / 'chapter2.md',
            self.dir / 'part1' / 'chapter3.md',
            self.dir / 'part2',
            self.dir / 'part2' / 'chapter1.md',
            self.dir / 'part2' / 'chapter2.md',
            self.dir / 'part2' / 'chapter3.md',
            self.dir / 'part3',
            self.dir / 'part3' / 'subdir',
            self.dir / 'part3' / 'subdir' / 'chapter1.md',
            self.dir / 'part3' / 'subdir' / 'chapter2.md',
            self.dir / 'part3' / 'subdir' / 'chapter3.md',
        ))

    async def test_include_only_top_level(self):
        book = await self.book_from_manifest('''
            title: Example book
            paths:
              include: ['*.md']
        ''')
        self.assertEqual(book.title, 'Example book')
        self.assertEqual(book.max_level, 2)
        self.assertPagePaths(book, (
            self.dir,
            self.dir / 'cover.md',
            self.dir / 'intro.md',
        ))

    async def test_include_only_part2(self):
        book = await self.book_from_manifest('''
            title: Example book
            paths:
              include: ['part2/*.md']
        ''')
        self.assertEqual(book.title, 'Example book')
        self.assertEqual(book.max_level, 3)
        self.assertPagePaths(book, (
            self.dir,
            self.dir / 'part2',
            self.dir / 'part2' / 'chapter1.md',
            self.dir / 'part2' / 'chapter2.md',
            self.dir / 'part2' / 'chapter3.md',
        ))

    async def test_include_only_chapters3(self):
        book = await self.book_from_manifest('''
            title: Example book
            paths:
                  include: ['**/chapter3.md']
        ''')
        self.assertEqual(book.title, 'Example book')
        self.assertEqual(book.max_level, 4)
        self.assertPagePaths(book, (
            self.dir,
            self.dir / 'part1',
            self.dir / 'part1' / 'chapter3.md',
            self.dir / 'part2',
            self.dir / 'part2' / 'chapter3.md',
            self.dir / 'part3',
            self.dir / 'part3' / 'subdir',
            self.dir / 'part3' / 'subdir' / 'chapter3.md',
        ))

    async def test_include_all_except_part2(self):
        book = await self.book_from_manifest('''
            title: Example book
            paths:
              include: ['**/*.md']
              exclude: ['**/part2/*.md']
        ''')
        self.assertEqual(book.title, 'Example book')
        self.assertEqual(book.max_level, 4)
        self.assertPagePaths(book, (
            self.dir,
            self.dir / 'cover.md',
            self.dir / 'intro.md',
            self.dir / 'part1',
            self.dir / 'part1' / 'chapter1.md',
            self.dir / 'part1' / 'chapter2.md',
            self.dir / 'part1' / 'chapter3.md',
            self.dir / 'part3',
            self.dir / 'part3' / 'subdir',
            self.dir / 'part3' / 'subdir' / 'chapter1.md',
            self.dir / 'part3' / 'subdir' / 'chapter2.md',
            self.dir / 'part3' / 'subdir' / 'chapter3.md',
        ))

    async def test_include_all_except_chapters3(self):
        book = await self.book_from_manifest('''
            title: Example book
            paths:
              include: ['**/*.md']
              exclude: ['**/chapter3.md']
        ''')
        self.assertEqual(book.title, 'Example book')
        self.assertEqual(book.max_level, 4)
        self.assertPagePaths(book, (
            self.dir,
            self.dir / 'cover.md',
            self.dir / 'intro.md',
            self.dir / 'part1',
            self.dir / 'part1' / 'chapter1.md',
            self.dir / 'part1' / 'chapter2.md',
            self.dir / 'part2',
            self.dir / 'part2' / 'chapter1.md',
            self.dir / 'part2' / 'chapter2.md',
            self.dir / 'part3',
            self.dir / 'part3' / 'subdir',
            self.dir / 'part3' / 'subdir' / 'chapter1.md',
            self.dir / 'part3' / 'subdir' / 'chapter2.md',
        ))


if __name__ == '__main__':
    main()

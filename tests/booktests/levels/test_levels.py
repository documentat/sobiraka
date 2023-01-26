from pathlib import Path
from unittest import main

from booktestcase import BookTestCase


class TestLevels(BookTestCase):
    def test_ids(self):
        ids = tuple(page.id for page in self.book.pages)
        self.assertSequenceEqual(ids, (
            '--',
            '--part1',
            '--part1--chapter1',
            '--part1--chapter2',
            '--part1--chapter3',
            '--part2',
            '--part2--chapter1',
            '--part2--chapter2',
            '--part2--chapter3',
            '--part2--chapter3--paragraph1',
            '--part2--chapter3--paragraph2',
            '--part2--chapter3--paragraph3',
        ))

    def test_max_level(self):
        self.assertEqual(self.book.max_level, 4)

    def test_levels(self):
        for path, level in (
                (Path() / '0-index.rst', 1),
                (Path() / 'part1' / '0-intro.rst', 2),
                (Path() / 'part1' / '1-chapter1.rst', 3),
                (Path() / 'part1' / '2-chapter2.rst', 3),
                (Path() / 'part1' / '3-chapter3.rst', 3),
                (Path() / 'part2' / '0-intro.rst', 2),
                (Path() / 'part2' / '1-chapter1.rst', 3),
                (Path() / 'part2' / '2-chapter2.rst', 3),
                (Path() / 'part2' / '3-chapter3' / '0.rst', 3),
                (Path() / 'part2' / '3-chapter3' / '1-paragraph1.rst', 4),
                (Path() / 'part2' / '3-chapter3' / '2-paragraph2.rst', 4),
                (Path() / 'part2' / '3-chapter3' / '3-paragraph3.rst', 4),
        ):
            with self.subTest(path):
                self.assertEqual(self.book.pages_by_path[path].level, level)

    def test_antilevels(self):
        for path, antilevel in (
                (Path() / '0-index.rst', 4),
                (Path() / 'part1' / '0-intro.rst', 3),
                (Path() / 'part1' / '1-chapter1.rst', 2),
                (Path() / 'part1' / '2-chapter2.rst', 2),
                (Path() / 'part1' / '3-chapter3.rst', 2),
                (Path() / 'part2' / '0-intro.rst', 3),
                (Path() / 'part2' / '1-chapter1.rst', 2),
                (Path() / 'part2' / '2-chapter2.rst', 2),
                (Path() / 'part2' / '3-chapter3' / '0.rst', 2),
                (Path() / 'part2' / '3-chapter3' / '1-paragraph1.rst', 1),
                (Path() / 'part2' / '3-chapter3' / '2-paragraph2.rst', 1),
                (Path() / 'part2' / '3-chapter3' / '3-paragraph3.rst', 1),
        ):
            with self.subTest(path):
                self.assertEqual(self.book.pages_by_path[path].antilevel, antilevel)


del BookTestCase


if __name__ == '__main__':
    main()

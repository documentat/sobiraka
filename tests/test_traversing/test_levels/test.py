from pathlib import Path
from unittest import main

from abstracttests.projecttestcase import ProjectTestCase


class TestLevels(ProjectTestCase):
    def test_ids(self):
        expected_ids = (
            'r',
            'r--part1',
            'r--part1--chapter1',
            'r--part1--chapter2',
            'r--part1--chapter3',
            'r--part2',
            'r--part2--chapter1',
            'r--part2--chapter2',
            'r--part2--chapter3',
            'r--part2--chapter3--paragraph1',
            'r--part2--chapter3--paragraph2',
            'r--part2--chapter3--paragraph3',
        )
        actual_ids = tuple(page.id for page in self.project.pages)
        self.assertSequenceEqual(expected_ids, actual_ids)

    def test_max_level(self):
        self.assertEqual(4, self.project.volumes[0].max_level)

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
                self.assertEqual(level, self.project.pages_by_path[path].level)

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
                self.assertEqual(antilevel, self.project.pages_by_path[path].antilevel)


del ProjectTestCase

if __name__ == '__main__':
    main()

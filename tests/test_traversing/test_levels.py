from unittest import main
from unittest.mock import Mock

from abstracttests.projecttestcase import ProjectTestCase
from sobiraka.models import FileSystem, IndexPage, Page, Project, Volume
from sobiraka.utils import RelativePath


class TestLevels(ProjectTestCase):
    def _init_project(self) -> Project:
        return Project(Mock(FileSystem), {
            RelativePath('src'): Volume({
                RelativePath() / '0-index.md': IndexPage(),
                RelativePath() / 'part1' / '0-intro.md': IndexPage('Part 1'),
                RelativePath() / 'part1' / '1-chapter1.md': Page('Chapter 1'),
                RelativePath() / 'part1' / '2-chapter2.md': Page('Chapter 2'),
                RelativePath() / 'part1' / '3-chapter3.md': Page('Chapter 3'),
                RelativePath() / 'part2' / '0-intro.md': IndexPage('Part 2'),
                RelativePath() / 'part2' / '1-chapter1.md': Page('Chapter 1'),
                RelativePath() / 'part2' / '2-chapter2.md': Page('Chapter 2'),
                RelativePath() / 'part2' / '3-chapter3' / '0.md': IndexPage('Chapter 3'),
                RelativePath() / 'part2' / '3-chapter3' / '1-paragraph1.md': Page('Paragraph 1'),
                RelativePath() / 'part2' / '3-chapter3' / '2-paragraph2.md': Page('Paragraph 2'),
                RelativePath() / 'part2' / '3-chapter3' / '3-paragraph3.md': Page('Paragraph 3'),
            })
        })

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

    def test_levels(self):
        for path, level in (
                (RelativePath() / 'src' / '0-index.md', 1),
                (RelativePath() / 'src' / 'part1' / '0-intro.md', 2),
                (RelativePath() / 'src' / 'part1' / '1-chapter1.md', 3),
                (RelativePath() / 'src' / 'part1' / '2-chapter2.md', 3),
                (RelativePath() / 'src' / 'part1' / '3-chapter3.md', 3),
                (RelativePath() / 'src' / 'part2' / '0-intro.md', 2),
                (RelativePath() / 'src' / 'part2' / '1-chapter1.md', 3),
                (RelativePath() / 'src' / 'part2' / '2-chapter2.md', 3),
                (RelativePath() / 'src' / 'part2' / '3-chapter3' / '0.md', 3),
                (RelativePath() / 'src' / 'part2' / '3-chapter3' / '1-paragraph1.md', 4),
                (RelativePath() / 'src' / 'part2' / '3-chapter3' / '2-paragraph2.md', 4),
                (RelativePath() / 'src' / 'part2' / '3-chapter3' / '3-paragraph3.md', 4),
        ):
            with self.subTest(path):
                self.assertEqual(level, self.project.pages_by_path[path].level)


del ProjectTestCase

if __name__ == '__main__':
    main()

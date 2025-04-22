from unittest import main

from abstracttests.projecttestcase import ProjectTestCase
from helpers.fakeproject import FakeProject, FakeVolume
from sobiraka.models import Project


class TestLevels(ProjectTestCase):
    def _init_project(self) -> Project:
        return FakeProject({
            'src': FakeVolume({
                'index.md': '',
                'part1': {
                    '0-intro.md': 'Part 1',
                    '1-chapter1.md': 'Chapter 1',
                    '2-chapter2.md': 'Chapter 2',
                    '3-chapter3.md': 'Chapter 3',
                },
                'part2': {
                    '0-intro.md': 'Part 2',
                    '1-chapter1.md': 'Chapter 1',
                    '2-chapter2.md': 'Chapter 2',
                    '3-chapter3': {
                        '0.md': 'Chapter 3',
                        '1-paragraph1.md': 'Paragraph 1',
                        '2-paragraph2.md': 'Paragraph 2',
                        '3-paragraph3.md': 'Paragraph 3',
                    },
                },
            }),
        })

    def test_levels(self):
        for location, level in {
            '/': 1,
            '/part1/': 2,
            '/part1/chapter1': 3,
            '/part1/chapter2': 3,
            '/part1/chapter3': 3,
            '/part2/': 2,
            '/part2/chapter1': 3,
            '/part2/chapter2': 3,
            '/part2/chapter3/': 3,
            '/part2/chapter3/paragraph1': 4,
            '/part2/chapter3/paragraph2': 4,
            '/part2/chapter3/paragraph3': 4,
        }.items():
            with self.subTest(location):
                page = self.project.get_volume().get_page_by_location(location)
                self.assertEqual(level, page.location.level)


del ProjectTestCase

if __name__ == '__main__':
    main()

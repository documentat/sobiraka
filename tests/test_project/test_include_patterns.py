from typing import Sequence
from unittest import main

from abstracttests.projecttestcase import ProjectTestCase
from helpers.fakeproject import FakeProject, FakeVolume
from sobiraka.models import Project, Status
from sobiraka.models.config import Config, Config_Paths
from sobiraka.utils import RelativePath


class TestIncludePatterns(ProjectTestCase):
    REQUIRE = Status.LOAD

    ROOT = ''
    INCLUDE = []
    EXCLUDE = []
    EXPECTED_LOCATIONS: Sequence[str]

    def _init_project(self) -> Project:
        config = Config(
            paths=Config_Paths(
                root=RelativePath(self.ROOT),
                include=self.INCLUDE,
                exclude=self.EXCLUDE,
            ),
        )
        return FakeProject({
            self.ROOT: FakeVolume(config, {
                'intro.md': '',
                'part1': {
                    'chapter1.md': '',
                    'chapter2.md': '',
                    'chapter3.md': '',
                },
                'part2': {
                    'chapter1.md': '',
                    'chapter2.md': '',
                    'chapter3.md': '',
                },
                'part3': {
                    'subdir': {
                        'chapter1.md': '',
                        'chapter2.md': '',
                        'chapter3.md': '',
                    },
                },
            })
        })

    def test_included_paths(self):
        actual_paths = tuple(str(p.location) for p in self.project.get_volume().root.all_pages())
        self.assertSequenceEqual(self.EXPECTED_LOCATIONS, actual_paths)


class TestIncludePatterns_Empty(TestIncludePatterns):
    EXPECTED_LOCATIONS = []


class TestIncludePatterns_All(TestIncludePatterns):
    INCLUDE = ['**/*.md']
    EXPECTED_LOCATIONS = (
        '/',
        '/intro',
        '/part1/',
        '/part1/chapter1',
        '/part1/chapter2',
        '/part1/chapter3',
        '/part2/',
        '/part2/chapter1',
        '/part2/chapter2',
        '/part2/chapter3',
        '/part3/',
        '/part3/subdir/',
        '/part3/subdir/chapter1',
        '/part3/subdir/chapter2',
        '/part3/subdir/chapter3',
    )


class TestIncludePatterns_OnlyTopLevel(TestIncludePatterns):
    INCLUDE = ['*.md']
    EXPECTED_LOCATIONS = (
        '/',
        '/intro',
    )


class TestIncludePatterns_OnlyPart2(TestIncludePatterns):
    INCLUDE = ['part2/*.md']
    EXPECTED_LOCATIONS = (
        '/',
        '/part2/',
        '/part2/chapter1',
        '/part2/chapter2',
        '/part2/chapter3',
    )


class TestIncludePatterns_OnlyChapter3(TestIncludePatterns):
    INCLUDE = ['**/chapter3.md']
    EXPECTED_LOCATIONS = (
        '/',
        '/part1/',
        '/part1/chapter3',
        '/part2/',
        '/part2/chapter3',
        '/part3/',
        '/part3/subdir/',
        '/part3/subdir/chapter3',
    )


class TestIncludePatterns_AllExceptPart2(TestIncludePatterns):
    INCLUDE = ['**/*.md']
    EXCLUDE = ['**/part2/chapter1.md', '**/part2/chapter2.md', '**/part2/chapter3.md']
    EXPECTED_LOCATIONS = (
        '/',
        '/intro',
        '/part1/',
        '/part1/chapter1',
        '/part1/chapter2',
        '/part1/chapter3',
        '/part3/',
        '/part3/subdir/',
        '/part3/subdir/chapter1',
        '/part3/subdir/chapter2',
        '/part3/subdir/chapter3',
    )


class TestIncludePatterns_AllExceptChapter3(TestIncludePatterns):
    INCLUDE = ['**/*.md']
    EXCLUDE = ['**/chapter3.md']
    EXPECTED_LOCATIONS = (
        '/',
        '/intro',
        '/part1/',
        '/part1/chapter1',
        '/part1/chapter2',
        '/part2/',
        '/part2/chapter1',
        '/part2/chapter2',
        '/part3/',
        '/part3/subdir/',
        '/part3/subdir/chapter1',
        '/part3/subdir/chapter2',
    )


for klass_name, klass in tuple(globals().items()):
    if isinstance(klass, type) and issubclass(klass, TestIncludePatterns) and klass is not TestIncludePatterns:
        klass_name = klass_name.replace('TestIncludePatterns_', 'TestIncludePatternsWithCustomRoot_')
        klass_bases = klass.__bases__
        klass_dict = klass.__dict__ | dict(ROOT='src')
        globals()[klass_name] = type(klass_name, klass.__bases__, klass_dict)

del ProjectTestCase, TestIncludePatterns

if __name__ == '__main__':
    main()

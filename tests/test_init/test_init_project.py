from pathlib import Path
from unittest import TestCase, main
from unittest.mock import Mock

from sobiraka.models import DirPage, FileSystem, Page, Project, Volume


class TestInitProject(TestCase):

    def test_with_fs_tuple(self):
        fs = Mock(FileSystem)
        vol1 = Volume((Path('page1.md'), Path('page2.md'), Path('page3.md')))
        vol2 = Volume((Path('page1.md'), Path('page2.md'), Path('page3.md')))
        vol3 = Volume((Path('page1.md'), Path('page2.md'), Path('page3.md')))
        project = Project(fs, (
            vol1,
            vol2,
            vol3,
        ))

        with self.subTest('fs'):
            self.assertIs(fs, project.fs)

        with self.subTest('volumes'):
            expected = vol1, vol2, vol3
            self.assertSequenceEqual(expected, project.volumes)

        with self.subTest('primary_volume'):
            self.assertIs(vol1, project.primary_volume)

    def test_with_fs_dict(self):
        fs = Mock(FileSystem)
        vol1 = Volume((Path('page1.md'), Path('page2.md'), Path('page3.md')))
        vol2 = Volume((Path('page1.md'), Path('page2.md'), Path('page3.md')))
        vol3 = Volume((Path('page1.md'), Path('page2.md'), Path('page3.md')))
        project = Project(fs, {
            Path('src1'): vol1,
            Path('src2'): vol2,
            Path('src3'): vol3,
        })

        with self.subTest('fs'):
            self.assertIs(fs, project.fs)

        with self.subTest('volumes'):
            expected = vol1, vol2, vol3
            self.assertSequenceEqual(expected, project.volumes)

        with self.subTest('primary_volume'):
            self.assertIs(vol1, project.primary_volume)

        with self.subTest('relative_roots'):
            expected = Path('src1'), Path('src2'), Path('src3')
            actual = tuple(v.relative_root for v in project.volumes)
            self.assertSequenceEqual(expected, actual)

        with self.subTest('roots'):
            expected = Path('src1'), Path('src2'), Path('src3')
            actual = tuple(v.relative_root for v in project.volumes)
            self.assertSequenceEqual(expected, actual)

        with self.subTest('pages_by_path'):
            expected = (
                (Path('src1'), DirPage(vol1, Path('.'))),
                (Path('src1/page1.md'), Page(vol1, Path('page1.md'))),
                (Path('src1/page2.md'), Page(vol1, Path('page2.md'))),
                (Path('src1/page3.md'), Page(vol1, Path('page3.md'))),
                (Path('src2'), DirPage(vol2, Path('.'))),
                (Path('src2/page1.md'), Page(vol2, Path('page1.md'))),
                (Path('src2/page2.md'), Page(vol2, Path('page2.md'))),
                (Path('src2/page3.md'), Page(vol2, Path('page3.md'))),
                (Path('src3'), DirPage(vol3, Path('.'))),
                (Path('src3/page1.md'), Page(vol3, Path('page1.md'))),
                (Path('src3/page2.md'), Page(vol3, Path('page2.md'))),
                (Path('src3/page3.md'), Page(vol3, Path('page3.md'))),
            )
            actual = tuple(project.pages_by_path.items())
            self.assertSequenceEqual(expected, actual)

        with self.subTest('pages'):
            expected = (
                DirPage(vol1, Path('.')),
                Page(vol1, Path('page1.md')),
                Page(vol1, Path('page2.md')),
                Page(vol1, Path('page3.md')),
                DirPage(vol2, Path('.')),
                Page(vol2, Path('page1.md')),
                Page(vol2, Path('page2.md')),
                Page(vol2, Path('page3.md')),
                DirPage(vol3, Path('.')),
                Page(vol3, Path('page1.md')),
                Page(vol3, Path('page2.md')),
                Page(vol3, Path('page3.md')),
            )
            actual = tuple(project.pages)
            self.assertSequenceEqual(expected, actual)


if __name__ == '__main__':
    main()

from unittest import TestCase, main
from unittest.mock import Mock

from sobiraka.models import DirPage, FileSystem, Page, Project, Volume
from sobiraka.utils import RelativePath


class TestInitProject(TestCase):

    def test_with_fs_tuple(self):
        vol1 = Volume({
            RelativePath('page1.md'): Page(),
            RelativePath('page2.md'): Page(),
            RelativePath('page3.md'): Page(),
        })
        vol2 = Volume({
            RelativePath('page1.md'): Page(),
            RelativePath('page2.md'): Page(),
            RelativePath('page3.md'): Page(),
        })
        vol3 = Volume({
            RelativePath('page1.md'): Page(),
            RelativePath('page2.md'): Page(),
            RelativePath('page3.md'): Page(),
        })

        fs = Mock(FileSystem)
        project = Project(fs, (vol1, vol2, vol3))

        with self.subTest('fs'):
            self.assertIs(fs, project.fs)

        with self.subTest('volumes'):
            expected = vol1, vol2, vol3
            self.assertSequenceEqual(expected, project.volumes)

        with self.subTest('primary_volume'):
            self.assertIs(None, project.primary_language)

    def test_with_fs_dict(self):
        vol1 = Volume({
            RelativePath('page1.md'): Page(),
            RelativePath('page2.md'): Page(),
            RelativePath('page3.md'): Page(),
        })
        vol2 = Volume({
            RelativePath('page1.md'): Page(),
            RelativePath('page2.md'): Page(),
            RelativePath('page3.md'): Page(),
        })
        vol3 = Volume({
            RelativePath('page1.md'): Page(),
            RelativePath('page2.md'): Page(),
            RelativePath('page3.md'): Page(),
        })

        fs = Mock(FileSystem)
        project = Project(fs, {
            RelativePath('src1'): vol1,
            RelativePath('src2'): vol2,
            RelativePath('src3'): vol3,
        })

        with self.subTest('fs'):
            self.assertIs(fs, project.fs)

        with self.subTest('volumes'):
            expected = vol1, vol2, vol3
            self.assertSequenceEqual(expected, project.volumes)

        with self.subTest('primary_language'):
            self.assertIs(None, project.primary_language)

        with self.subTest('relative_roots'):
            expected = RelativePath('src1'), RelativePath('src2'), RelativePath('src3')
            actual = tuple(v.relative_root for v in project.volumes)
            self.assertSequenceEqual(expected, actual)

        with self.subTest('roots'):
            expected = RelativePath('src1'), RelativePath('src2'), RelativePath('src3')
            actual = tuple(v.relative_root for v in project.volumes)
            self.assertSequenceEqual(expected, actual)

        with self.subTest('pages_by_path'):
            expected = (
                (RelativePath('src1'), DirPage(vol1, RelativePath('.'))),
                (RelativePath('src1/page1.md'), Page(vol1, RelativePath('page1.md'))),
                (RelativePath('src1/page2.md'), Page(vol1, RelativePath('page2.md'))),
                (RelativePath('src1/page3.md'), Page(vol1, RelativePath('page3.md'))),
                (RelativePath('src2'), DirPage(vol2, RelativePath('.'))),
                (RelativePath('src2/page1.md'), Page(vol2, RelativePath('page1.md'))),
                (RelativePath('src2/page2.md'), Page(vol2, RelativePath('page2.md'))),
                (RelativePath('src2/page3.md'), Page(vol2, RelativePath('page3.md'))),
                (RelativePath('src3'), DirPage(vol3, RelativePath('.'))),
                (RelativePath('src3/page1.md'), Page(vol3, RelativePath('page1.md'))),
                (RelativePath('src3/page2.md'), Page(vol3, RelativePath('page2.md'))),
                (RelativePath('src3/page3.md'), Page(vol3, RelativePath('page3.md'))),
            )
            actual = tuple(project.pages_by_path.items())
            self.assertSequenceEqual(expected, actual)

        with self.subTest('pages'):
            expected = (
                DirPage(vol1, RelativePath('.')),
                Page(vol1, RelativePath('page1.md')),
                Page(vol1, RelativePath('page2.md')),
                Page(vol1, RelativePath('page3.md')),
                DirPage(vol2, RelativePath('.')),
                Page(vol2, RelativePath('page1.md')),
                Page(vol2, RelativePath('page2.md')),
                Page(vol2, RelativePath('page3.md')),
                DirPage(vol3, RelativePath('.')),
                Page(vol3, RelativePath('page1.md')),
                Page(vol3, RelativePath('page2.md')),
                Page(vol3, RelativePath('page3.md')),
            )
            actual = tuple(project.pages)
            self.assertSequenceEqual(expected, actual)


if __name__ == '__main__':
    main()

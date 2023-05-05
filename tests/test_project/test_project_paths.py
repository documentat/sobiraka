import re
from pathlib import Path
from tempfile import TemporaryDirectory
from textwrap import dedent
from unittest import IsolatedAsyncioTestCase, main

from sobiraka.models import Project
from sobiraka.models.load import load_project


class TestProjectPaths(IsolatedAsyncioTestCase):
    maxDiff = None

    def prepare_dirs(self):
        temp_dir: str = self.enterContext(TemporaryDirectory(prefix='sobiraka-test-'))
        self.root = Path(temp_dir)
        self.manifest_path = self.root / 'project.yaml'

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

    async def project_from_yaml(self, data_yaml: str) -> Project:
        data_yaml = dedent(data_yaml)
        if self.path_to_root:
            data_yaml = re.sub(r'^paths:\n', f'paths:\n  root: {self.path_to_root}\n', data_yaml, flags=re.MULTILINE)
        self.manifest_path.parent.mkdir(parents=True, exist_ok=True)
        self.manifest_path.write_text(dedent(data_yaml))
        return load_project(self.manifest_path)

    def assertPagePaths(self, project: Project, expected_paths: tuple[Path, ...]):
        actual_paths = tuple(p.path for p in project.pages)
        self.assertSequenceEqual(expected_paths, actual_paths)

    ################################################################################

    async def test_empty(self):
        project = await self.project_from_yaml('''
            paths:
              include: []
        ''')
        self.assertEqual(0, project.volumes[0].max_level)
        self.assertPagePaths(project, ())

    async def test_include_all(self):
        project = await self.project_from_yaml('''
            paths:
              include: ['**/*.md']
        ''')
        self.assertEqual(4, project.volumes[0].max_level)
        self.assertPagePaths(project, (
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
        project = await self.project_from_yaml('''
            paths:
              include: ['*.md']
        ''')
        self.assertEqual(2, project.volumes[0].max_level)
        self.assertPagePaths(project, (
            self.root,
            self.root / 'intro.md',
        ))

    async def test_include_only_part2(self):
        project = await self.project_from_yaml('''
            paths:
              include: ['part2/*.md']
        ''')
        self.assertEqual(3, project.volumes[0].max_level)
        self.assertPagePaths(project, (
            self.root,
            self.root / 'part2',
            self.root / 'part2' / 'chapter1.md',
            self.root / 'part2' / 'chapter2.md',
            self.root / 'part2' / 'chapter3.md',
        ))

    async def test_include_only_chapters3(self):
        project = await self.project_from_yaml('''
            paths:
              include: ['**/chapter3.md']
        ''')
        self.assertEqual(4, project.volumes[0].max_level)
        self.assertPagePaths(project, (
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
        project = await self.project_from_yaml('''
            paths:
              include: ['**/*.md']
              exclude: ['**/part2/*.md']
        ''')
        self.assertEqual(4, project.volumes[0].max_level)
        self.assertPagePaths(project, (
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
        project = await self.project_from_yaml('''
            paths:
              include: ['**/*.md']
              exclude: ['**/chapter3.md']
        ''')
        self.assertEqual(4, project.volumes[0].max_level)
        self.assertPagePaths(project, (
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


class TestProjectPaths_CustomRootAbsolute(TestProjectPaths):
    def prepare_dirs(self):
        super().prepare_dirs()
        temp_dir: str = self.enterContext(TemporaryDirectory(prefix='sobiraka-test-'))
        self.manifest_path = Path(temp_dir) / 'project.yaml'
        self.path_to_root = str(self.root)


class TestProjectPaths_CustomRootInside(TestProjectPaths):
    def prepare_dirs(self):
        super().prepare_dirs()
        self.root /= 'src'
        self.path_to_root = 'src'


class TestProjectPaths_CustomRootOutside(TestProjectPaths):
    def prepare_dirs(self):
        super().prepare_dirs()
        self.manifest_path = self.root / 'manifest' / 'project.yaml'
        self.path_to_root = '..'


if __name__ == '__main__':
    main()
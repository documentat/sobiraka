from tempfile import TemporaryDirectory
from unittest import IsolatedAsyncioTestCase, main

from sobiraka.models import Project, RealFileSystem
from sobiraka.models.load import load_project_from_dict
from sobiraka.utils import AbsolutePath, RelativePath


class TestIncludePatterns(IsolatedAsyncioTestCase):
    maxDiff = None

    def prepare_dirs(self):
        # pylint: disable=consider-using-with
        temp_dir: str = self.enterContext(TemporaryDirectory(prefix='sobiraka-test-'))
        self.fs = RealFileSystem(AbsolutePath(temp_dir))
        self.root = AbsolutePath(temp_dir)

    async def asyncSetUp(self):
        self.root: AbsolutePath
        self.manifest_path: AbsolutePath
        self.path_to_root: str | None = None

        self.prepare_dirs()
        self.paths: tuple[AbsolutePath, ...] = (
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

    def prepare_project(self, manifest: dict) -> Project:
        if self.path_to_root:
            manifest['paths']['root'] = self.path_to_root
        return load_project_from_dict(manifest, fs=self.fs)

    def assertPagePaths(self, project: Project, expected_paths: tuple[RelativePath, ...]):
        actual_paths = tuple(p.path_in_volume for p in project.pages)
        self.assertSequenceEqual(expected_paths, actual_paths)

    ################################################################################

    async def test_empty(self):
        project = self.prepare_project({
            'paths': {
                'include': [],
            }
        })
        self.assertPagePaths(project, ())

    async def test_include_all(self):
        project = self.prepare_project({
            'paths': {
                'include': ['**/*.md'],
            }
        })
        self.assertPagePaths(project, (
            RelativePath(),
            RelativePath() / 'intro.md',
            RelativePath() / 'part1',
            RelativePath() / 'part1' / 'chapter1.md',
            RelativePath() / 'part1' / 'chapter2.md',
            RelativePath() / 'part1' / 'chapter3.md',
            RelativePath() / 'part2',
            RelativePath() / 'part2' / 'chapter1.md',
            RelativePath() / 'part2' / 'chapter2.md',
            RelativePath() / 'part2' / 'chapter3.md',
            RelativePath() / 'part3',
            RelativePath() / 'part3' / 'subdir',
            RelativePath() / 'part3' / 'subdir' / 'chapter1.md',
            RelativePath() / 'part3' / 'subdir' / 'chapter2.md',
            RelativePath() / 'part3' / 'subdir' / 'chapter3.md',
        ))

    async def test_include_only_top_level(self):
        project = self.prepare_project({
            'paths': {
                'include': ['*.md'],
            }
        })
        self.assertPagePaths(project, (
            RelativePath(),
            RelativePath() / 'intro.md',
        ))

    async def test_include_only_part2(self):
        project = self.prepare_project({
            'paths': {
                'include': ['part2/*.md'],
            }
        })
        self.assertPagePaths(project, (
            RelativePath(),
            RelativePath() / 'part2',
            RelativePath() / 'part2' / 'chapter1.md',
            RelativePath() / 'part2' / 'chapter2.md',
            RelativePath() / 'part2' / 'chapter3.md',
        ))

    async def test_include_only_chapters3(self):
        project = self.prepare_project({
            'paths': {
                'include': ['**/chapter3.md'],
            }
        })
        self.assertPagePaths(project, (
            RelativePath(),
            RelativePath() / 'part1',
            RelativePath() / 'part1' / 'chapter3.md',
            RelativePath() / 'part2',
            RelativePath() / 'part2' / 'chapter3.md',
            RelativePath() / 'part3',
            RelativePath() / 'part3' / 'subdir',
            RelativePath() / 'part3' / 'subdir' / 'chapter3.md',
        ))

    async def test_include_all_except_part2(self):
        project = self.prepare_project({
            'paths': {
                'include': ['**/*.md'],
                'exclude': ['**/part2/*.md'],
            }
        })
        self.assertPagePaths(project, (
            RelativePath(),
            RelativePath() / 'intro.md',
            RelativePath() / 'part1',
            RelativePath() / 'part1' / 'chapter1.md',
            RelativePath() / 'part1' / 'chapter2.md',
            RelativePath() / 'part1' / 'chapter3.md',
            RelativePath() / 'part3',
            RelativePath() / 'part3' / 'subdir',
            RelativePath() / 'part3' / 'subdir' / 'chapter1.md',
            RelativePath() / 'part3' / 'subdir' / 'chapter2.md',
            RelativePath() / 'part3' / 'subdir' / 'chapter3.md',
        ))

    async def test_include_all_except_chapters3(self):
        project = self.prepare_project({
            'paths': {
                'include': ['**/*.md'],
                'exclude': ['**/chapter3.md'],
            }
        })
        self.assertPagePaths(project, (
            RelativePath(),
            RelativePath() / 'intro.md',
            RelativePath() / 'part1',
            RelativePath() / 'part1' / 'chapter1.md',
            RelativePath() / 'part1' / 'chapter2.md',
            RelativePath() / 'part2',
            RelativePath() / 'part2' / 'chapter1.md',
            RelativePath() / 'part2' / 'chapter2.md',
            RelativePath() / 'part3',
            RelativePath() / 'part3' / 'subdir',
            RelativePath() / 'part3' / 'subdir' / 'chapter1.md',
            RelativePath() / 'part3' / 'subdir' / 'chapter2.md',
        ))


class TestIncludePatterns_CustomRoot(TestIncludePatterns):
    def prepare_dirs(self):
        super().prepare_dirs()
        self.root /= 'src'
        self.path_to_root = 'src'


if __name__ == '__main__':
    main()

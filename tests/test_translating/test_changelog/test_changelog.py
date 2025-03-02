from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from shutil import copy, copytree
from subprocess import PIPE, run
from tempfile import TemporaryDirectory
from unittest import TestCase, main

from helpers import clean_directory
from sobiraka.translating import changelog
from sobiraka.utils import AbsolutePath


class TestChangelog(TestCase):
    maxDiff = None

    def setUp(self):
        # pylint: disable=consider-using-with
        self.repo_dir = AbsolutePath(self.enterContext(TemporaryDirectory(prefix='sobiraka-test-')))

    def _git(self, command: str, *args: str):
        result = run(('git', command, *args), cwd=self.repo_dir, text=True, check=False, stdout=PIPE)
        return result.stdout.rstrip()

    def test_all(self):
        for subdir in sorted(AbsolutePath(__file__).parent.iterdir()):
            if not subdir.is_dir() or subdir.name.startswith('_'):
                continue

            with self.subTest(subdir.name):
                try:
                    self._git('init', '--initial-branch', 'master')
                    self._git('config', 'user.name', 'Tester')
                    self._git('config', 'user.email', 'tester@example.com')
                    for rev in ('R1', 'R2'):
                        copytree(subdir / rev, self.repo_dir, dirs_exist_ok=True, copy_function=copy)
                        self._git('add', '.')
                        self._git('commit', '--message', f'Revision {rev}')
                        self._git('tag', rev)

                    with redirect_stdout(StringIO()) as _stdout, redirect_stderr(StringIO()) as _stderr:
                        changelog(self.repo_dir / 'project.yaml', 'R1', 'R2')
                    self.assertEqual('', _stdout.getvalue())
                    actual = _stderr.getvalue().rstrip()

                    expected = (subdir / 'expected.txt').read_text('utf-8').rstrip()
                    self.assertEqual(expected, actual)

                finally:
                    clean_directory(self.repo_dir)


if __name__ == '__main__':
    main()

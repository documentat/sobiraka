from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from textwrap import dedent
from unittest import TestCase, main
from unittest.mock import Mock

from sobiraka.models import FileSystem, IndexPage, Page, PageMeta, Project, TranslationStatus, Version, Volume
from sobiraka.translating import check_translations


class TestVersioning(TestCase):
    def setUp(self):
        super().setUp()
        self.project = Project(Mock(FileSystem), {
            Path('src-en'): Volume('en', '', {
                Path('0-index.md'): IndexPage(PageMeta(version=Version(1, 0)), ''),
                Path('aaa.md'): Page(PageMeta(version=Version(3, 4)), ''),
                Path('bbb.md'): Page(PageMeta(version=Version(6, 2)), ''),
            }),
            Path('src-ru'): Volume('ru', '', {
                Path('0-index.md'): IndexPage(PageMeta(version=Version(1, 0)), ''),
                Path('aaa.md'): Page(PageMeta(version=Version(3, 2)), ''),
                Path('bbb.md'): Page(PageMeta(version=Version(5, 2)), ''),
            })
        })

    def test_get_translation(self):
        data: dict[str, dict[Path, Path]] = {
            'ru': {
                Path('src-en/0-index.md'): Path('src-ru/0-index.md'),
                Path('src-en/aaa.md'): Path('src-ru/aaa.md'),
                Path('src-en/bbb.md'): Path('src-ru/bbb.md'),
            },
            'en': {
                Path('src-ru/0-index.md'): Path('src-en/0-index.md'),
                Path('src-ru/aaa.md'): Path('src-en/aaa.md'),
                Path('src-ru/bbb.md'): Path('src-en/bbb.md'),
            },
        }
        for lang, subdata in data.items():
            with self.subTest(lang):
                for path, expected in subdata.items():
                    page = self.project.pages_by_path[path]
                    with self.subTest(page):
                        page_tr = self.project.get_translation(page, lang)
                        actual = page_tr.path_in_project
                        self.assertEqual(expected, actual)

    def test_original(self):
        data: dict[Path, Path] = {
            Path('src-en/0-index.md'): Path('src-en/0-index.md'),
            Path('src-en/aaa.md'): Path('src-en/aaa.md'),
            Path('src-en/bbb.md'): Path('src-en/bbb.md'),

            Path('src-ru/0-index.md'): Path('src-en/0-index.md'),
            Path('src-ru/aaa.md'): Path('src-en/aaa.md'),
            Path('src-ru/bbb.md'): Path('src-en/bbb.md'),
        }
        for path, expected_path in data.items():
            page = self.project.pages_by_path[path]
            expected = self.project.pages_by_path[expected_path]
            with self.subTest(page):
                actual = page.original
                self.assertEqual(expected, actual)

    def test_version(self):
        data: dict[Path, Version] = {
            Path('src-en/0-index.md'): Version(1, 0),
            Path('src-en/aaa.md'): Version(3, 4),
            Path('src-en/bbb.md'): Version(6, 2),

            Path('src-ru/0-index.md'): Version(1, 0),
            Path('src-ru/aaa.md'): Version(3, 2),
            Path('src-ru/bbb.md'): Version(5, 2),
        }
        for path, expected in data.items():
            page = self.project.pages_by_path[path]
            with self.subTest(page):
                actual = page.meta.version
                self.assertEqual(expected, actual)

    def test_translation_status(self):
        data: dict[Path, TranslationStatus] = {
            Path('src-en/0-index.md'): TranslationStatus.UPTODATE,
            Path('src-en/aaa.md'): TranslationStatus.UPTODATE,
            Path('src-en/bbb.md'): TranslationStatus.UPTODATE,

            Path('src-ru/0-index.md'): TranslationStatus.UPTODATE,
            Path('src-ru/aaa.md'): TranslationStatus.MODIFIED,
            Path('src-ru/bbb.md'): TranslationStatus.OUTDATED,
        }
        for path, expected in data.items():
            page = self.project.pages_by_path[path]
            with self.subTest(page):
                actual = page.translation_status
                self.assertEqual(expected, actual)

    def test_check_translations(self):
        expected = dedent('''
        en:
          This is the primary volume
          Pages: 3
        ru:
          Up-to-date pages: 1
          Modified pages: 1
            src-ru/aaa.md
          Outdated pages: 1
            src-ru/bbb.md
        ''').lstrip()

        for strict in (False, True):
            with self.subTest(strict=strict):
                with redirect_stdout(StringIO()) as _stdout, redirect_stderr(StringIO()) as _stderr:
                    check_translations(self.project, strict=strict)
                    self.assertEqual('', _stdout.getvalue())
                    self.assertEqual(expected, _stderr.getvalue())


if __name__ == '__main__':
    main()

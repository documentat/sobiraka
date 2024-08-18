from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from textwrap import dedent
from unittest import TestCase, main
from unittest.mock import Mock

from sobiraka.models import FileSystem, IndexPage, Page, PageMeta, Project, TranslationStatus, Version, Volume
from sobiraka.translating import check_translations
from sobiraka.utils import RelativePath


class TestVersioning(TestCase):
    def setUp(self):
        super().setUp()
        self.project = Project(Mock(FileSystem), {
            RelativePath('src-en'): Volume('en', '', {
                RelativePath('0-index.md'): IndexPage(PageMeta(version=Version(1, 0)), ''),
                RelativePath('aaa.md'): Page(PageMeta(version=Version(3, 4)), ''),
                RelativePath('bbb.md'): Page(PageMeta(version=Version(6, 2)), ''),
            }),
            RelativePath('src-ru'): Volume('ru', '', {
                RelativePath('0-index.md'): IndexPage(PageMeta(version=Version(1, 0)), ''),
                RelativePath('aaa.md'): Page(PageMeta(version=Version(3, 2)), ''),
                RelativePath('bbb.md'): Page(PageMeta(version=Version(5, 2)), ''),
            })
        })

    def test_get_translation(self):
        data: dict[str, dict[RelativePath, RelativePath]] = {
            'ru': {
                RelativePath('src-en/0-index.md'): RelativePath('src-ru/0-index.md'),
                RelativePath('src-en/aaa.md'): RelativePath('src-ru/aaa.md'),
                RelativePath('src-en/bbb.md'): RelativePath('src-ru/bbb.md'),
            },
            'en': {
                RelativePath('src-ru/0-index.md'): RelativePath('src-en/0-index.md'),
                RelativePath('src-ru/aaa.md'): RelativePath('src-en/aaa.md'),
                RelativePath('src-ru/bbb.md'): RelativePath('src-en/bbb.md'),
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
        data: dict[RelativePath, RelativePath] = {
            RelativePath('src-en/0-index.md'): RelativePath('src-en/0-index.md'),
            RelativePath('src-en/aaa.md'): RelativePath('src-en/aaa.md'),
            RelativePath('src-en/bbb.md'): RelativePath('src-en/bbb.md'),

            RelativePath('src-ru/0-index.md'): RelativePath('src-en/0-index.md'),
            RelativePath('src-ru/aaa.md'): RelativePath('src-en/aaa.md'),
            RelativePath('src-ru/bbb.md'): RelativePath('src-en/bbb.md'),
        }
        for path, expected_path in data.items():
            page = self.project.pages_by_path[path]
            expected = self.project.pages_by_path[expected_path]
            with self.subTest(page):
                actual = page.original
                self.assertEqual(expected, actual)

    def test_version(self):
        data: dict[RelativePath, Version] = {
            RelativePath('src-en/0-index.md'): Version(1, 0),
            RelativePath('src-en/aaa.md'): Version(3, 4),
            RelativePath('src-en/bbb.md'): Version(6, 2),

            RelativePath('src-ru/0-index.md'): Version(1, 0),
            RelativePath('src-ru/aaa.md'): Version(3, 2),
            RelativePath('src-ru/bbb.md'): Version(5, 2),
        }
        for path, expected in data.items():
            page = self.project.pages_by_path[path]
            with self.subTest(page):
                actual = page.meta.version
                self.assertEqual(expected, actual)

    def test_translation_status(self):
        data: dict[RelativePath, TranslationStatus] = {
            RelativePath('src-en/0-index.md'): TranslationStatus.UPTODATE,
            RelativePath('src-en/aaa.md'): TranslationStatus.UPTODATE,
            RelativePath('src-en/bbb.md'): TranslationStatus.UPTODATE,

            RelativePath('src-ru/0-index.md'): TranslationStatus.UPTODATE,
            RelativePath('src-ru/aaa.md'): TranslationStatus.MODIFIED,
            RelativePath('src-ru/bbb.md'): TranslationStatus.OUTDATED,
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

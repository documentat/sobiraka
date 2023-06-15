from pathlib import Path
from unittest import main

from abstracttests.projectdirtestcase import ProjectDirTestCase
from sobiraka.models import TranslationStatus, Version


class TestVersioning(ProjectDirTestCase):

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
            Path('src-en/0-index.md'): TranslationStatus.LATEST,
            Path('src-en/aaa.md'): TranslationStatus.LATEST,
            Path('src-en/bbb.md'): TranslationStatus.LATEST,

            Path('src-ru/0-index.md'): TranslationStatus.LATEST,
            Path('src-ru/aaa.md'): TranslationStatus.IMPERFECT,
            Path('src-ru/bbb.md'): TranslationStatus.OUTDATED,
        }
        for path, expected in data.items():
            page = self.project.pages_by_path[path]
            with self.subTest(page):
                actual = page.translation_status
                self.assertEqual(expected, actual)


del ProjectDirTestCase

if __name__ == '__main__':
    main()

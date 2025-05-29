from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from textwrap import dedent
from unittest import main

from typing_extensions import override

from abstracttests.projecttestcase import ProjectTestCase
from helpers.fakeproject import FakeProject, FakeVolume
from sobiraka.models import Project, Status, TranslationStatus, Version
from sobiraka.models.config import Config, Config_Paths
from sobiraka.translating import check_translations
from sobiraka.utils import RelativePath


class TestVersioning(ProjectTestCase):
    REQUIRE = Status.PARSE

    @override
    def _init_project(self) -> Project:
        project = FakeProject({
            'src-en': FakeVolume(
                Config(paths=Config_Paths(root=RelativePath('src-en'))),
                {
                    '0-index.md': '---\nversion: 1.0\n---',
                    'aaa.md': '---\nversion: 3.4\n---',
                    'bbb.md': '---\nversion: 6.2\n---',
                }),
            'src-ru': FakeVolume(
                Config(paths=Config_Paths(root=RelativePath('src-ru'))),
                {
                    '0-index.md': '---\nversion: 1.0\n---',
                    'aaa.md': '---\nversion: 3.2\n---',
                    'bbb.md': '---\nversion: 5.2\n---',
                })
        })

        project.volumes[0].lang = 'en'
        project.volumes[0].codename = None

        project.volumes[1].lang = 'ru'
        project.volumes[1].codename = None

        project.primary_language = 'en'
        return project

    @override
    async def _process(self):
        await super()._process()
        self.index_en, self.aaa_en, self.bbb_en = self.project.volumes[0].root.all_pages()
        self.index_ru, self.aaa_ru, self.bbb_ru = self.project.volumes[1].root.all_pages()

    def test_get_translation(self):
        data = {
            'ru': {
                self.index_en: self.index_ru,
                self.aaa_en: self.aaa_ru,
                self.bbb_en: self.bbb_ru,
            },
            'en': {
                self.index_ru: self.index_en,
                self.aaa_ru: self.aaa_en,
                self.bbb_ru: self.bbb_en,
            },
        }
        for lang, subdata in data.items():
            with self.subTest(lang):
                for page, expected in subdata.items():
                    with self.subTest(page):
                        actual = self.project.get_translation(page, lang)
                        self.assertIs(expected, actual)

    def test_original(self):
        data = {
            self.index_en: self.index_en,
            self.aaa_en: self.aaa_en,
            self.bbb_en: self.bbb_en,

            self.index_ru: self.index_en,
            self.aaa_ru: self.aaa_en,
            self.bbb_ru: self.bbb_en,
        }
        for page, expected in data.items():
            with self.subTest(page):
                actual = page.original
                self.assertEqual(expected, actual)

    def test_version(self):
        data = {
            self.index_en: Version(1, 0),
            self.aaa_en: Version(3, 4),
            self.bbb_en: Version(6, 2),

            self.index_ru: Version(1, 0),
            self.aaa_ru: Version(3, 2),
            self.bbb_ru: Version(5, 2),
        }
        for page, expected in data.items():
            with self.subTest(page):
                actual = page.meta.version
                self.assertEqual(expected, actual)

    def test_translation_status(self):
        data = {
            self.index_en: TranslationStatus.UPTODATE,
            self.aaa_en: TranslationStatus.UPTODATE,
            self.bbb_en: TranslationStatus.UPTODATE,

            self.index_ru: TranslationStatus.UPTODATE,
            self.aaa_ru: TranslationStatus.MODIFIED,
            self.bbb_ru: TranslationStatus.OUTDATED,
        }
        for page, expected in data.items():
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

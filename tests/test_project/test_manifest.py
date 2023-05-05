from pathlib import Path
from textwrap import dedent
from unittest import TestCase, main

import yaml

from sobiraka.models import Volume
from sobiraka.models.load import load_project_from_dict


class _TestManifest(TestCase):
    YAML = NotImplemented

    def setUp(self):
        manifest = yaml.safe_load(dedent(self.YAML))
        self.project = load_project_from_dict(manifest, base=Path('/BASE'))


class TestManifest_1L_1V(_TestManifest):
    def setUp(self):
        super().setUp()
        self.volume: Volume = self.project.volumes[0]

    def test_codename(self):
        self.assertEqual('vol1', self.volume.codename)

    def test_lang(self):
        self.assertEqual('en', self.volume.lang)

    def test_title(self):
        self.assertEqual('Documentation', self.volume.title)

    def test_root(self):
        self.assertEqual(Path('/BASE/src/en'), self.volume.root)

    def test_include(self):
        self.assertEqual(('one', 'two', 'three'), self.volume.paths.include)

    def test_resources_prefix(self):
        self.assertEqual(Path('/BASE/img'), self.volume.html.resources_prefix)

    YAML = '''
        languages:
            en:
                volumes:
                    vol1:
                        title: Documentation
                        paths:
                            root: src/en
                            include: [one, two, three]
                        html:
                            resources_prefix: img
    '''


class TestManifest_1L_1VUnderscored(TestManifest_1L_1V):
    def test_codename(self):
        self.assertEqual(None, self.volume.codename)

    YAML = '''
        languages:
            en:
                volumes:
                    DEFAULT:
                        title: Documentation
                        paths:
                            root: src/en
                            include: [one, two, three]
                        html:
                            resources_prefix: img
    '''


class TestManifest_1L_1VFlat(TestManifest_1L_1V):
    def test_codename(self):
        self.assertEqual(None, self.volume.codename)

    YAML = '''
        languages:
            en:
                title: Documentation
                paths:
                    root: src/en
                    include: [one, two, three]
                html:
                    resources_prefix: img
    '''


class TestManifest_1LUnderscore_1V(TestManifest_1L_1V):
    def test_lang(self):
        self.assertEqual(None, self.volume.lang)

    YAML = '''
        languages:
            DEFAULT:
                volumes:
                    vol1:
                        title: Documentation
                        paths:
                            root: src/en
                            include: [one, two, three]
                        html:
                            resources_prefix: img
    '''


class TestManifest_1LUnderscore_1VUnderscore(TestManifest_1L_1V):
    def test_codename(self):
        self.assertEqual(None, self.volume.codename)

    def test_lang(self):
        self.assertEqual(None, self.volume.lang)

    YAML = '''
        languages:
            DEFAULT:
                volumes:
                    DEFAULT:
                        title: Documentation
                        paths:
                            root: src/en
                            include: [one, two, three]
                        html:
                            resources_prefix: img
    '''


class TestManifest_1LUnderscore_1VFlat(TestManifest_1L_1V):
    def test_codename(self):
        self.assertEqual(None, self.volume.codename)

    def test_lang(self):
        self.assertEqual(None, self.volume.lang)

    YAML = '''
        languages:
            DEFAULT:
                title: Documentation
                paths:
                    root: src/en
                    include: [one, two, three]
                html:
                    resources_prefix: img
    '''


class TestManifest_1LFlat_1V(TestManifest_1L_1V):
    def test_lang(self):
        self.assertEqual(None, self.volume.lang)

    YAML = '''
        volumes:
            vol1:
                title: Documentation
                paths:
                    root: src/en
                    include: [one, two, three]
                html:
                    resources_prefix: img
    '''


class TestManifest_1LFlat_1VUnderscore(TestManifest_1L_1V):
    def test_codename(self):
        self.assertEqual(None, self.volume.codename)

    def test_lang(self):
        self.assertEqual(None, self.volume.lang)

    YAML = '''
        volumes:
            DEFAULT:
                title: Documentation
                paths:
                    root: src/en
                    include: [one, two, three]
                html:
                    resources_prefix: img
    '''


class TestManifest_1LFlat_1VFlat(TestManifest_1L_1V):
    def test_codename(self):
        self.assertEqual(None, self.volume.codename)

    def test_lang(self):
        self.assertEqual(None, self.volume.lang)

    YAML = '''
        title: Documentation
        paths:
            root: src/en
            include: [one, two, three]
        html:
            resources_prefix: img
    '''


class TestManifest_2L_2V(_TestManifest):
    def test_codename(self):
        expected_data = 'vol1', 'vol2', 'vol1', 'vol2'
        for expected, volume in zip(expected_data, self.project.volumes, strict=True):
            with self.subTest(volume.codename):
                self.assertEqual(expected, volume.codename)

    def test_lang(self):
        expected_data = 'en', 'en', 'ru', 'ru'
        for expected, volume in zip(expected_data, self.project.volumes, strict=True):
            with self.subTest(volume.codename):
                self.assertEqual(expected, volume.lang)

    def test_title(self):
        expected_data = 'Documentation', 'Documentation', 'Документация', 'Документация'
        for expected, volume in zip(expected_data, self.project.volumes, strict=True):
            with self.subTest(volume.codename):
                self.assertEqual(expected, volume.title)

    def test_root(self):
        expected_data = Path('/BASE/src/en'), Path('/BASE/src/en'), Path('/BASE/src/ru'), Path('/BASE/src/ru')
        for expected, volume in zip(expected_data, self.project.volumes, strict=True):
            with self.subTest(volume.codename):
                self.assertEqual(expected, volume.root)

    def test_include(self):
        expected_data = ('one', 'two', 'three'), ('four', 'five', 'six'), ('one', 'two', 'three'), (
            'four', 'five', 'six')
        for expected, volume in zip(expected_data, self.project.volumes, strict=True):
            with self.subTest(volume.codename):
                self.assertEqual(expected, volume.paths.include)

    def test_resources_prefix(self):
        expected_data = 4 * (Path('/BASE/img'),)
        for expected, volume in zip(expected_data, self.project.volumes, strict=True):
            with self.subTest(volume.codename):
                self.assertEqual(expected, volume.html.resources_prefix)

    YAML = '''
        languages:
            en:
                volumes:
                    vol1:
                        title: Documentation
                        paths:
                            root: src/en
                            include: [one, two, three]
                        html:
                            resources_prefix: img
                    vol2:
                        title: Documentation
                        paths:
                            root: src/en
                            include: [four, five, six]
                        html:
                            resources_prefix: img
            ru:
                volumes:
                    vol1:
                        title: Документация
                        paths:
                            root: src/ru
                            include: [one, two, three]
                        html:
                            resources_prefix: img
                    vol2:
                        title: Документация
                        paths:
                            root: src/ru
                            include: [four, five, six]
                        html:
                            resources_prefix: img
    '''


class TestManifest_2L_2V_LanguageDefaults(TestManifest_2L_2V):
    YAML = '''
        languages:
            DEFAULT:
                volumes:
                    DEFAULT:
                        html:
                            resources_prefix: img
            en:
                volumes:
                    vol1:
                        title: Documentation
                        paths:
                            root: src/en
                            include: [one, two, three]
                    vol2:
                        title: Documentation
                        paths:
                            root: src/en
                            include: [four, five, six]
            ru:
                volumes:
                    vol1:
                        title: Документация
                        paths:
                            root: src/ru
                            include: [one, two, three]
                    vol2:
                        title: Документация
                        paths:
                            root: src/ru
                            include: [four, five, six]
    '''


class TestManifest_2L_2V_VolumeDefaults(TestManifest_2L_2V):
    YAML = '''
        languages:
            en:
                volumes:
                    DEFAULT:
                        title: Documentation
                    vol1:
                        paths:
                            root: src/en
                            include: [one, two, three]
                        html:
                            resources_prefix: img
                    vol2:
                        paths:
                            root: src/en
                            include: [four, five, six]
                        html:
                            resources_prefix: img
            ru:
                volumes:
                    DEFAULT:
                        title: Документация
                    vol1:
                        paths:
                            root: src/ru
                            include: [one, two, three]
                        html:
                            resources_prefix: img
                    vol2:
                        paths:
                            root: src/ru
                            include: [four, five, six]
                        html:
                            resources_prefix: img
    '''


class TestManifest_2L_2V_AllDefaults(TestManifest_2L_2V):
    YAML = '''
        languages:
            DEFAULT:
                volumes:
                    DEFAULT:
                        html:
                            resources_prefix: img
            en:
                volumes:
                    DEFAULT:
                        title: Documentation
                    vol1:
                        paths:
                            root: src/en
                            include: [one, two, three]
                    vol2:
                        paths:
                            root: src/en
                            include: [four, five, six]
            ru:
                volumes:
                    DEFAULT:
                        title: Документация
                    vol1:
                        paths:
                            root: src/ru
                            include: [one, two, three]
                    vol2:
                        paths:
                            root: src/ru
                            include: [four, five, six]
    '''


del _TestManifest

if __name__ == '__main__':
    main()
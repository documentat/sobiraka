from abc import ABCMeta, abstractmethod
from pathlib import Path
from unittest import TestCase, main

from sobiraka.models import Volume
from sobiraka.models.load import load_project_from_str


class _TestManifest(TestCase, metaclass=ABCMeta):
    YAML = NotImplemented

    def setUp(self):
        self.project = load_project_from_str(self.YAML, base=Path('/BASE'))

    @abstractmethod
    def test_lang(self): ...

    @abstractmethod
    def test_codename(self): ...

    @abstractmethod
    def test_autoprefix(self): ...

    @abstractmethod
    def test_title(self): ...

    @abstractmethod
    def test_root(self): ...

    @abstractmethod
    def test_include(self): ...

    @abstractmethod
    def test_resources_prefix(self): ...

    def test_primary_volume(self):
        self.assertIs(self.project.volumes[0], self.project.primary_volume)


class TestManifest_1L_1V(_TestManifest):
    def setUp(self):
        super().setUp()
        self.volume: Volume = self.project.volumes[0]

    def test_lang(self):
        self.assertEqual('en', self.volume.lang)

    def test_codename(self):
        self.assertEqual('vol1', self.volume.codename)

    def test_autoprefix(self):
        self.assertEqual('en/vol1', self.volume.autoprefix)

    def test_title(self):
        self.assertEqual('Documentation', self.volume.config.title)

    def test_root(self):
        self.assertEqual(Path('src/en'), self.volume.relative_root)

    def test_include(self):
        self.assertEqual(('one', 'two', 'three'), self.volume.config.paths.include)

    def test_resources_prefix(self):
        self.assertEqual('img', self.volume.config.html.resources_prefix)

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

    def test_autoprefix(self):
        self.assertEqual('en', self.volume.autoprefix)

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

    def test_autoprefix(self):
        self.assertEqual('en', self.volume.autoprefix)

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

    def test_autoprefix(self):
        self.assertEqual('vol1', self.volume.autoprefix)

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
    def test_lang(self):
        self.assertEqual(None, self.volume.lang)

    def test_codename(self):
        self.assertEqual(None, self.volume.codename)

    def test_autoprefix(self):
        self.assertEqual(None, self.volume.autoprefix)

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
    def test_lang(self):
        self.assertEqual(None, self.volume.lang)

    def test_codename(self):
        self.assertEqual(None, self.volume.codename)

    def test_autoprefix(self):
        self.assertEqual(None, self.volume.autoprefix)

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

    def test_autoprefix(self):
        self.assertEqual('vol1', self.volume.autoprefix)

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
    def test_lang(self):
        self.assertEqual(None, self.volume.lang)

    def test_codename(self):
        self.assertEqual(None, self.volume.codename)

    def test_autoprefix(self):
        self.assertEqual(None, self.volume.autoprefix)

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
    def test_lang(self):
        self.assertEqual(None, self.volume.lang)

    def test_codename(self):
        self.assertEqual(None, self.volume.codename)

    def test_autoprefix(self):
        self.assertEqual(None, self.volume.autoprefix)

    YAML = '''
        title: Documentation
        paths:
            root: src/en
            include: [one, two, three]
        html:
            resources_prefix: img
    '''


class TestManifest_2L_2V(_TestManifest):
    def test_lang(self):
        expected_data = 'en', 'en', 'ru', 'ru'
        for i, (expected, volume) in enumerate(zip(expected_data, self.project.volumes, strict=True)):
            with self.subTest(f'{i} - {expected}'):
                self.assertEqual(expected, volume.lang)

    def test_codename(self):
        expected_data = 'vol1', 'vol2', 'vol1', 'vol2'
        for i, (expected, volume) in enumerate(zip(expected_data, self.project.volumes, strict=True)):
            with self.subTest(f'{i} - {expected}'):
                self.assertEqual(expected, volume.codename)

    def test_autoprefix(self):
        expected_data = 'en/vol1', 'en/vol2', 'ru/vol1', 'ru/vol2'
        for i, (expected, volume) in enumerate(zip(expected_data, self.project.volumes, strict=True)):
            with self.subTest(f'{i} - {expected}'):
                self.assertEqual(expected, volume.autoprefix)

    def test_title(self):
        expected_data = 'Documentation', 'Documentation', 'Документация', 'Документация'
        for i, (expected, volume) in enumerate(zip(expected_data, self.project.volumes, strict=True)):
            with self.subTest(f'{i} - {expected}'):
                self.assertEqual(expected, volume.config.title)

    def test_root(self):
        expected_data = Path('src/en'), Path('src/en'), Path('src/ru'), Path('src/ru')
        for i, (expected, volume) in enumerate(zip(expected_data, self.project.volumes, strict=True)):
            with self.subTest(f'{i} - {expected}'):
                self.assertEqual(expected, volume.relative_root)

    def test_include(self):
        expected_data = ('one', 'two', 'three'), ('four', 'five', 'six'), ('one', 'two', 'three'), (
            'four', 'five', 'six')
        for i, (expected, volume) in enumerate(zip(expected_data, self.project.volumes, strict=True)):
            with self.subTest(f'{i} - {expected}'):
                self.assertEqual(expected, volume.config.paths.include)

    def test_resources_prefix(self):
        expected_data = 4 * ('img',)
        for i, (expected, volume) in enumerate(zip(expected_data, self.project.volumes, strict=True)):
            with self.subTest(f'{i} - {expected}'):
                self.assertEqual(expected, volume.config.html.resources_prefix)

    def test_primary_volume(self):
        self.assertEqual('ru/vol1', self.project.primary_volume.autoprefix)

    YAML = '''
        primary: ru/vol1
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
        primary: ru/vol1
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
        primary: ru/vol1
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
        primary: ru/vol1
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

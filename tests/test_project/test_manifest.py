from abc import ABCMeta, abstractmethod
from unittest import TestCase, main
from unittest.mock import Mock

from sobiraka.models import Document, FileSystem
from sobiraka.models.load import load_project_from_str
from sobiraka.utils import RelativePath


class _TestManifest(TestCase, metaclass=ABCMeta):
    YAML = NotImplemented

    def setUp(self):
        self.project = load_project_from_str(self.YAML, fs=Mock(FileSystem))

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

    def test_primary_language(self):
        self.assertIs(self.project.documents[0].lang, self.project.primary_language)


class TestManifest_1L_1V(_TestManifest):
    def setUp(self):
        super().setUp()
        self.document: Document = self.project.documents[0]

    def test_lang(self):
        self.assertEqual('en', self.document.lang)

    def test_codename(self):
        self.assertEqual('doc1', self.document.codename)

    def test_autoprefix(self):
        self.assertEqual('en/doc1', self.document.autoprefix)

    def test_title(self):
        self.assertEqual('Documentation', self.document.config.title)

    def test_root(self):
        self.assertEqual(RelativePath('src/en'), self.document.root_path)

    def test_include(self):
        self.assertEqual(('one', 'two', 'three'), self.document.config.paths.include)

    def test_resources_prefix(self):
        self.assertEqual('img', self.document.config.web.resources_prefix)

    YAML = '''
        languages:
            en:
                documents:
                    doc1:
                        title: Documentation
                        paths:
                            root: src/en
                            include: [one, two, three]
                        web:
                            resources_prefix: img
    '''


class TestManifest_1L_1VDefault(TestManifest_1L_1V):
    def test_codename(self):
        self.assertEqual(None, self.document.codename)

    def test_autoprefix(self):
        self.assertEqual('en', self.document.autoprefix)

    YAML = '''
        languages:
            en:
                documents:
                    DEFAULT:
                        title: Documentation
                        paths:
                            root: src/en
                            include: [one, two, three]
                        web:
                            resources_prefix: img
    '''


class TestManifest_1L_1VFlat(TestManifest_1L_1V):
    def test_codename(self):
        self.assertEqual(None, self.document.codename)

    def test_autoprefix(self):
        self.assertEqual('en', self.document.autoprefix)

    YAML = '''
        languages:
            en:
                title: Documentation
                paths:
                    root: src/en
                    include: [one, two, three]
                web:
                    resources_prefix: img
    '''


class TestManifest_1LDefault_1V(TestManifest_1L_1V):
    def test_lang(self):
        self.assertEqual(None, self.document.lang)

    def test_autoprefix(self):
        self.assertEqual('doc1', self.document.autoprefix)

    YAML = '''
        languages:
            DEFAULT:
                documents:
                    doc1:
                        title: Documentation
                        paths:
                            root: src/en
                            include: [one, two, three]
                        web:
                            resources_prefix: img
    '''


class TestManifest_1LDefault_1VDefault(TestManifest_1L_1V):
    def test_lang(self):
        self.assertEqual(None, self.document.lang)

    def test_codename(self):
        self.assertEqual(None, self.document.codename)

    def test_autoprefix(self):
        self.assertEqual(None, self.document.autoprefix)

    YAML = '''
        languages:
            DEFAULT:
                documents:
                    DEFAULT:
                        title: Documentation
                        paths:
                            root: src/en
                            include: [one, two, three]
                        web:
                            resources_prefix: img
    '''


class TestManifest_1LDefault_1VFlat(TestManifest_1L_1V):
    def test_lang(self):
        self.assertEqual(None, self.document.lang)

    def test_codename(self):
        self.assertEqual(None, self.document.codename)

    def test_autoprefix(self):
        self.assertEqual(None, self.document.autoprefix)

    YAML = '''
        languages:
            DEFAULT:
                title: Documentation
                paths:
                    root: src/en
                    include: [one, two, three]
                web:
                    resources_prefix: img
    '''


class TestManifest_1LFlat_1V(TestManifest_1L_1V):
    def test_lang(self):
        self.assertEqual(None, self.document.lang)

    def test_autoprefix(self):
        self.assertEqual('doc1', self.document.autoprefix)

    YAML = '''
        documents:
            doc1:
                title: Documentation
                paths:
                    root: src/en
                    include: [one, two, three]
                web:
                    resources_prefix: img
    '''


class TestManifest_1LFlat_1VDefault(TestManifest_1L_1V):
    def test_lang(self):
        self.assertEqual(None, self.document.lang)

    def test_codename(self):
        self.assertEqual(None, self.document.codename)

    def test_autoprefix(self):
        self.assertEqual(None, self.document.autoprefix)

    YAML = '''
        documents:
            DEFAULT:
                title: Documentation
                paths:
                    root: src/en
                    include: [one, two, three]
                web:
                    resources_prefix: img
    '''


class TestManifest_1LFlat_1VFlat(TestManifest_1L_1V):
    def test_lang(self):
        self.assertEqual(None, self.document.lang)

    def test_codename(self):
        self.assertEqual(None, self.document.codename)

    def test_autoprefix(self):
        self.assertEqual(None, self.document.autoprefix)

    YAML = '''
        title: Documentation
        paths:
            root: src/en
            include: [one, two, three]
        web:
            resources_prefix: img
    '''


class TestManifest_2L_2V(_TestManifest):
    def test_lang(self):
        expected_data = 'en', 'en', 'ru', 'ru'
        for i, (expected, document) in enumerate(zip(expected_data, self.project.documents, strict=True)):
            with self.subTest(f'{i} - {expected}'):
                self.assertEqual(expected, document.lang)

    def test_codename(self):
        expected_data = 'doc1', 'doc2', 'doc1', 'doc2'
        for i, (expected, document) in enumerate(zip(expected_data, self.project.documents, strict=True)):
            with self.subTest(f'{i} - {expected}'):
                self.assertEqual(expected, document.codename)

    def test_autoprefix(self):
        expected_data = 'en/doc1', 'en/doc2', 'ru/doc1', 'ru/doc2'
        for i, (expected, document) in enumerate(zip(expected_data, self.project.documents, strict=True)):
            with self.subTest(f'{i} - {expected}'):
                self.assertEqual(expected, document.autoprefix)

    def test_title(self):
        expected_data = 'Documentation', 'Documentation', 'Документация', 'Документация'
        for i, (expected, document) in enumerate(zip(expected_data, self.project.documents, strict=True)):
            with self.subTest(f'{i} - {expected}'):
                self.assertEqual(expected, document.config.title)

    def test_root(self):
        expected_data = map(RelativePath, ('src/en', 'src/en', 'src/ru', 'src/ru'))
        for i, (expected, document) in enumerate(zip(expected_data, self.project.documents, strict=True)):
            with self.subTest(f'{i} - {expected}'):
                self.assertEqual(expected, document.root_path)

    def test_include(self):
        expected_data = ('one', 'two', 'three'), ('four', 'five', 'six'), ('one', 'two', 'three'), (
            'four', 'five', 'six')
        for i, (expected, document) in enumerate(zip(expected_data, self.project.documents, strict=True)):
            with self.subTest(f'{i} - {expected}'):
                self.assertEqual(expected, document.config.paths.include)

    def test_resources_prefix(self):
        expected_data = 4 * ('img',)
        for i, (expected, document) in enumerate(zip(expected_data, self.project.documents, strict=True)):
            with self.subTest(f'{i} - {expected}'):
                self.assertEqual(expected, document.config.web.resources_prefix)

    def test_primary_language(self):
        self.assertEqual('ru', self.project.primary_language)

    YAML = '''
        primary_language: ru
        languages:
            en:
                documents:
                    doc1:
                        title: Documentation
                        paths:
                            root: src/en
                            include: [one, two, three]
                        web:
                            resources_prefix: img
                    doc2:
                        title: Documentation
                        paths:
                            root: src/en
                            include: [four, five, six]
                        web:
                            resources_prefix: img
            ru:
                documents:
                    doc1:
                        title: Документация
                        paths:
                            root: src/ru
                            include: [one, two, three]
                        web:
                            resources_prefix: img
                    doc2:
                        title: Документация
                        paths:
                            root: src/ru
                            include: [four, five, six]
                        web:
                            resources_prefix: img
    '''


class TestManifest_2L_2V_LanguageDefaults(TestManifest_2L_2V):
    YAML = '''
        primary_language: ru
        languages:
            DEFAULT:
                documents:
                    DEFAULT:
                        web:
                            resources_prefix: img
            en:
                documents:
                    doc1:
                        title: Documentation
                        paths:
                            root: src/en
                            include: [one, two, three]
                    doc2:
                        title: Documentation
                        paths:
                            root: src/en
                            include: [four, five, six]
            ru:
                documents:
                    doc1:
                        title: Документация
                        paths:
                            root: src/ru
                            include: [one, two, three]
                    doc2:
                        title: Документация
                        paths:
                            root: src/ru
                            include: [four, five, six]
    '''


class TestManifest_2L_2V_DocumentDefaults(TestManifest_2L_2V):
    YAML = '''
        primary_language: ru
        languages:
            en:
                documents:
                    DEFAULT:
                        title: Documentation
                    doc1:
                        paths:
                            root: src/en
                            include: [one, two, three]
                        web:
                            resources_prefix: img
                    doc2:
                        paths:
                            root: src/en
                            include: [four, five, six]
                        web:
                            resources_prefix: img
            ru:
                documents:
                    DEFAULT:
                        title: Документация
                    doc1:
                        paths:
                            root: src/ru
                            include: [one, two, three]
                        web:
                            resources_prefix: img
                    doc2:
                        paths:
                            root: src/ru
                            include: [four, five, six]
                        web:
                            resources_prefix: img
    '''


class TestManifest_2L_2V_AllDefaults(TestManifest_2L_2V):
    YAML = '''
        primary_language: ru
        languages:
            DEFAULT:
                documents:
                    DEFAULT:
                        web:
                            resources_prefix: img
            en:
                documents:
                    DEFAULT:
                        title: Documentation
                    doc1:
                        paths:
                            root: src/en
                            include: [one, two, three]
                    doc2:
                        paths:
                            root: src/en
                            include: [four, five, six]
            ru:
                documents:
                    DEFAULT:
                        title: Документация
                    doc1:
                        paths:
                            root: src/ru
                            include: [one, two, three]
                    doc2:
                        paths:
                            root: src/ru
                            include: [four, five, six]
    '''


del _TestManifest

if __name__ == '__main__':
    main()

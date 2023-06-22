from pathlib import Path
from unittest import TestCase
from unittest.mock import Mock

from sobiraka.models import Page, Project, Volume
from sobiraka.models.config import Config, Config_Paths


class TestInitVolume(TestCase):

    def test_with_paths(self):
        volume = Volume((
            Path('page1.md'),
            Path('page2.md'),
            Path('page3.md'),
        ))
        volume.project = Mock(Project, base=Path('/project'))

        with self.subTest('lang'):
            self.assertIsNone(volume.lang)

        with self.subTest('codename'):
            self.assertIsNone(volume.codename)

        with self.subTest('config'):
            self.assertEqual(Config(), volume.config)

        with self.subTest('pages'):
            expected = (
                Path('.'),
                Path('page1.md'),
                Path('page2.md'),
                Path('page3.md'),
            )
            actual = tuple(p.path_in_volume for p in volume.pages)
            self.assertSequenceEqual(expected, actual)

        with self.subTest('pages_by_path'):
            expected = (
                Path('.'),
                Path('page1.md'),
                Path('page2.md'),
                Path('page3.md'),
            )
            actual = tuple(volume.pages_by_path.keys())
            self.assertSequenceEqual(expected, actual)

    def test_with_lang_codename_paths(self):
        volume = Volume('en', 'example', (
            Path('page1.md'),
            Path('page2.md'),
            Path('page3.md'),
        ))
        volume.project = Mock(Project, base=Path('/project'))

        with self.subTest('lang'):
            self.assertEqual('en', volume.lang)

        with self.subTest('codename'):
            self.assertEqual('example', volume.codename)

        with self.subTest('config'):
            self.assertEqual(Config(), volume.config)

        with self.subTest('pages'):
            expected = (
                Path('.'),
                Path('page1.md'),
                Path('page2.md'),
                Path('page3.md'),
            )
            actual = tuple(p.path_in_volume for p in volume.pages)
            self.assertSequenceEqual(expected, actual)

        with self.subTest('pages_by_path'):
            expected = (
                Path('.'),
                Path('page1.md'),
                Path('page2.md'),
                Path('page3.md'),
            )
            actual = tuple(volume.pages_by_path.keys())
            self.assertSequenceEqual(expected, actual)

    def test_with_pages(self):
        volume = Volume({
            Path('page1.md'): (page1 := Page()),
            Path('page2.md'): (page2 := Page()),
            Path('page3.md'): (page3 := Page()),
        })
        volume.project = Mock(Project, base=Path('/project'))

        with self.subTest('lang'):
            self.assertIsNone(volume.lang)

        with self.subTest('codename'):
            self.assertIsNone(volume.codename)

        with self.subTest('config'):
            self.assertEqual(volume.config, Config())

        with self.subTest('pages'):
            expected = (
                Path('.'),
                Path('page1.md'),
                Path('page2.md'),
                Path('page3.md'),
            )
            actual = tuple(p.path_in_volume for p in volume.pages)
            self.assertSequenceEqual(expected, actual)

        with self.subTest('pages_by_path'):
            expected = (
                Path('.'),
                Path('page1.md'),
                Path('page2.md'),
                Path('page3.md'),
            )
            actual = tuple(volume.pages_by_path.keys())
            self.assertSequenceEqual(expected, actual)

    def test_with_lang_codename_pages(self):
        volume = Volume('en', 'example', {
            Path('page1.md'): (page1 := Page()),
            Path('page2.md'): (page2 := Page()),
            Path('page3.md'): (page3 := Page()),
        })
        volume.project = Mock(Project, base=Path('/project'))

        with self.subTest('lang'):
            self.assertEqual('en', volume.lang)

        with self.subTest('codename'):
            self.assertEqual('example', volume.codename)

        with self.subTest('config'):
            self.assertEqual(volume.config, Config())

        with self.subTest('pages'):
            expected = (
                Path('.'),
                Path('page1.md'),
                Path('page2.md'),
                Path('page3.md'),
            )
            actual = tuple(p.path_in_volume for p in volume.pages)
            self.assertSequenceEqual(expected, actual)

        with self.subTest('pages_by_path'):
            expected = (
                Path('.'),
                Path('page1.md'),
                Path('page2.md'),
                Path('page3.md'),
            )
            actual = tuple(volume.pages_by_path.keys())
            self.assertSequenceEqual(expected, actual)

    def test_with_lang_codename_config(self):
        root = Path('/project')
        config = Config(paths=Config_Paths(root=root))
        volume = Volume('en', 'example', config)

        with self.subTest('lang'):
            self.assertEqual('en', volume.lang)

        with self.subTest('codename'):
            self.assertEqual('example', volume.codename)

        with self.subTest('config'):
            self.assertEqual(config, volume.config)

    def test_with_project_lang_codename_config(self):
        project = Mock(Project)
        config = Config()
        volume = Volume(project, 'en', 'example', config)

        with self.subTest('project'):
            self.assertIs(project, volume.project)

        with self.subTest('lang'):
            self.assertEqual('en', volume.lang)

        with self.subTest('codename'):
            self.assertEqual('example', volume.codename)

        with self.subTest('config'):
            self.assertEqual(Config(), volume.config)


if __name__ == '__main__':
    main()

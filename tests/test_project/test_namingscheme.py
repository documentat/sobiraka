from math import inf
from pathlib import Path
from unittest import TestCase
from unittest.mock import Mock

from sobiraka.models import FileSystem, NamingScheme, Project, Volume
from sobiraka.models.config import Config, Config_Paths
from sobiraka.models.load import _load_volume


class TestDefaultNamingScheme(TestCase):
    def setUp(self):
        volume = _load_volume('en', 'vol', {}, Mock(FileSystem))
        self.scheme: NamingScheme = volume.config.paths.naming_scheme

    def test_index_and_stem(self):
        actual = self.scheme.get_index_and_stem('16-example.md')
        self.assertEqual((16, 'example'), actual)

    def test_only_index(self):
        actual = self.scheme.get_index_and_stem('1.md')
        self.assertEqual((1, '1'), actual)

    def test_only_stem(self):
        actual = self.scheme.get_index_and_stem('example.md')
        self.assertEqual((inf, 'example'), actual)

    def test_ordering(self):
        project = Project(
            Mock(FileSystem),
            {
                Path('.'): Volume(
                    Config(
                        paths=Config_Paths(
                            root=Path('.'),
                            naming_scheme=self.scheme,
                        )),
                    (
                        Path('2-aaa/3-ddd'),
                        Path('2-kkk.md'),
                        Path('1-ppp.md'),
                        Path('2-aaa/9-sss/5-eee.md'),
                        Path('2-aaa/3-ddd/5-nnn.md'),
                        Path('2-aaa/5-nnn.md'),
                        Path('2-aaa/2-kkk.md'),
                        Path('2-aaa/9-sss/3-www.md'),
                    )),
            })
        volume = project.volumes[0]
        expected_order = (
            Path('.'),
            Path('1-ppp.md'),
            Path('2-aaa'),
            Path('2-aaa/2-kkk.md'),
            Path('2-aaa/3-ddd'),
            Path('2-aaa/3-ddd/5-nnn.md'),
            Path('2-aaa/5-nnn.md'),
            Path('2-aaa/9-sss'),
            Path('2-aaa/9-sss/3-www.md'),
            Path('2-aaa/9-sss/5-eee.md'),
            Path('2-kkk.md'),
        )
        actual_order = tuple(volume.pages_by_path.keys())
        self.assertSequenceEqual(expected_order, actual_order)


class TestBackwardsNamingScheme(TestCase):
    def setUp(self):
        self.scheme = NamingScheme((r'(?P<stem>[a-z]+)? (?P<index>\d+)?',))

    def test_ordering(self):
        project = Project(
            Mock(FileSystem),
            {
                Path('.'): Volume(
                    Config(
                        paths=Config_Paths(
                            root=Path('.'),
                            naming_scheme=self.scheme,
                        )),
                    (
                        Path('a2/d3'),
                        Path('k2.md'),
                        Path('p1.md'),
                        Path('a2/s9/e5.md'),
                        Path('a2/d3/n5.md'),
                        Path('a2/n5.md'),
                        Path('a2/k2.md'),
                        Path('a2/s9/w3.md'),
                    )),
            })
        volume = project.volumes[0]
        expected_order = (
            Path('.'),
            Path('p1.md'),
            Path('a2'),
            Path('a2/k2.md'),
            Path('a2/d3'),
            Path('a2/d3/n5.md'),
            Path('a2/n5.md'),
            Path('a2/s9'),
            Path('a2/s9/w3.md'),
            Path('a2/s9/e5.md'),
            Path('k2.md'),
        )
        actual_order = tuple(volume.pages_by_path.keys())
        self.assertSequenceEqual(expected_order, actual_order)

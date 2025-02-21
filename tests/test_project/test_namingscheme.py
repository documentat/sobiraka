import re
from math import inf
from os.path import splitext
from unittest import TestCase, main
from unittest.mock import Mock

from sobiraka.models import FileNameData, FileSystem, NamingScheme, Project, Volume
from sobiraka.models.config import Config, Config_Paths
from sobiraka.models.load import load_volume
from sobiraka.utils import RelativePath


class AbstractNamingSchemeTest(TestCase):
    naming_scheme: NamingScheme
    parsing_results: dict[str, FileNameData]
    ordering_original: tuple[RelativePath, ...]
    ordering_expected: tuple[RelativePath, ...]

    def test_parse(self):
        for filename, expected in self.parsing_results.items():
            with self.subTest(splitext(filename)[0]):
                actual = self.naming_scheme.parse(filename)
                self.assertEqual(expected, actual)

    def test_ordering(self):
        project = Project(
            Mock(FileSystem),
            {
                RelativePath('.'): Volume(
                    Config(
                        paths=Config_Paths(
                            root=RelativePath('.'),
                            naming_scheme=self.naming_scheme,
                        )),
                    self.ordering_original),
            })
        volume = project.volumes[0]
        ordering_actual = tuple(volume.pages_by_path.keys())
        self.assertSequenceEqual(self.ordering_expected, ordering_actual)


class TestDefaultNamingScheme(AbstractNamingSchemeTest):
    def setUp(self):
        volume = load_volume('en', 'vol', {}, Mock(FileSystem))
        self.naming_scheme = volume.config.paths.naming_scheme

    parsing_results = {
        '16-example.md': FileNameData(16, 'example'),
        '1.md': FileNameData(1, '1'),
        'example.md': FileNameData(inf, 'example'),
        '0.md': FileNameData(0, '0', True),
        '0-index.md': FileNameData(0, 'index', True),
        'index.md': FileNameData(inf, 'index', True),
    }

    ordering_original = (
        RelativePath('2-aaa/3-ddd'),
        RelativePath('2-kkk.md'),
        RelativePath('1-ppp.md'),
        RelativePath('2-aaa/9-sss/5-eee.md'),
        RelativePath('2-aaa/3-ddd/5-nnn.md'),
        RelativePath('2-aaa/5-nnn.md'),
        RelativePath('2-aaa/2-kkk.md'),
        RelativePath('2-aaa/9-sss/3-www.md'),
        RelativePath('2-aaa/index.md'),
        RelativePath('2-aaa/unnumbered.md'),
    )
    ordering_expected = (
        RelativePath('.'),
        RelativePath('1-ppp.md'),
        RelativePath('2-aaa'),
        RelativePath('2-aaa/index.md'),
        RelativePath('2-aaa/2-kkk.md'),
        RelativePath('2-aaa/3-ddd'),
        RelativePath('2-aaa/3-ddd/5-nnn.md'),
        RelativePath('2-aaa/5-nnn.md'),
        RelativePath('2-aaa/9-sss'),
        RelativePath('2-aaa/9-sss/3-www.md'),
        RelativePath('2-aaa/9-sss/5-eee.md'),
        RelativePath('2-aaa/unnumbered.md'),
        RelativePath('2-kkk.md'),
    )


class TestInvertedNamingScheme(AbstractNamingSchemeTest):
    """
    Test a weird naming scheme that puts the number at the end.
    """
    naming_scheme = NamingScheme((
        re.compile(r'(?P<stem>[a-z]+) (?P<pos>\d+)', re.VERBOSE),
    ))

    parsing_results = {
        'a1.md': FileNameData(1, 'a'),
        'b2.md': FileNameData(2, 'b'),
        'c3.md': FileNameData(3, 'c'),
    }

    ordering_original = (
        RelativePath('a2/d3'),
        RelativePath('k2.md'),
        RelativePath('p1.md'),
        RelativePath('a2/s9/e5.md'),
        RelativePath('a2/d3/n5.md'),
        RelativePath('a2/n5.md'),
        RelativePath('a2/k2.md'),
        RelativePath('a2/s9/w3.md'),
    )

    ordering_expected = (
        RelativePath('.'),
        RelativePath('p1.md'),
        RelativePath('a2'),
        RelativePath('a2/k2.md'),
        RelativePath('a2/d3'),
        RelativePath('a2/d3/n5.md'),
        RelativePath('a2/n5.md'),
        RelativePath('a2/s9'),
        RelativePath('a2/s9/w3.md'),
        RelativePath('a2/s9/e5.md'),
        RelativePath('k2.md'),
    )


del AbstractNamingSchemeTest

if __name__ == '__main__':
    main()

import re
from abc import ABCMeta
from math import inf
from os.path import splitext
from typing import Sequence, final
from unittest import main

from typing_extensions import override

from abstracttests.projecttestcase import ProjectTestCase
from helpers.fakeproject import FakeProject, FakeVolume
from sobiraka.models import FileNameData, NamingScheme, Project, Status
from sobiraka.models.config import Config, Config_Paths
from sobiraka.utils import RelativePath


class TestNamingScheme(ProjectTestCase, metaclass=ABCMeta):
    REQUIRE = Status.LOAD

    naming_scheme: NamingScheme
    parsing_examples: dict[str, FileNameData]
    expected_ordering: Sequence[str]

    @final
    def _init_config(self):
        return Config(
            paths=Config_Paths(
                root=RelativePath('src'),
                naming_scheme=self.naming_scheme,
            )
        )

    def test_parse(self):
        for filename, expected in self.parsing_examples.items():
            with self.subTest(splitext(filename)[0]):
                actual = self.naming_scheme.parse(filename)
                self.assertEqual(expected, actual)

    def test_ordering(self):
        actual_ordering = tuple(str(p.location) for p in self.project.get_volume().root.all_pages())
        self.assertSequenceEqual(self.expected_ordering, actual_ordering)


class TestDefaultNamingScheme(TestNamingScheme):
    naming_scheme = NamingScheme()

    parsing_examples = {
        '16-example.md': FileNameData(16, 'example'),
        '1.md': FileNameData(1, '1'),
        'example.md': FileNameData(inf, 'example'),
        '0.md': FileNameData(0, '0', True),
        '0-index.md': FileNameData(0, 'index', True),
        'index.md': FileNameData(inf, 'index', True),
    }

    @override
    def _init_project(self) -> Project:
        return FakeProject({
            'src': FakeVolume(self._init_config(), {
                '2-aaa/3-ddd/index.md': '',
                '2-kkk.md': '',
                '1-ppp.md': '',
                '2-aaa/9-sss/5-eee.md': '',
                '2-aaa/3-ddd/5-nnn.md': '',
                '2-aaa/5-nnn.md': '',
                '2-aaa/2-kkk.md': '',
                '2-aaa/9-sss/3-www.md': '',
                '2-aaa/unnumbered.md': '',
            })
        })

    expected_ordering = (
        '/',
        '/ppp',
        '/aaa/',
        '/aaa/kkk',
        '/aaa/ddd/',
        '/aaa/ddd/nnn',
        '/aaa/nnn',
        '/aaa/sss/',
        '/aaa/sss/www',
        '/aaa/sss/eee',
        '/aaa/unnumbered',
        '/kkk',
    )


class TestInvertedNamingScheme(TestNamingScheme):
    """
    Test a weird naming scheme that puts the number at the end.
    """
    naming_scheme = NamingScheme((
        re.compile(r'(?P<is_main>index)           ', re.VERBOSE),
        re.compile(r'(?P<stem>[a-z]+) (?P<pos>\d+)', re.VERBOSE),
    ))

    parsing_examples = {
        'a1.md': FileNameData(1, 'a'),
        'b2.md': FileNameData(2, 'b'),
        'c3.md': FileNameData(3, 'c'),
    }

    @override
    def _init_project(self) -> Project:
        return FakeProject({
            'src': FakeVolume(self._init_config(), {
                'a2/d3/index.md': '',
                'k2.md': '',
                'p1.md': '',
                'a2/s9/e5.md': '',
                'a2/d3/n5.md': '',
                'a2/n5.md': '',
                'a2/k2.md': '',
                'a2/s9/w3.md': '',
            })
        })

    expected_ordering = (
        '/',
        '/p',
        '/a/',
        '/a/k',
        '/a/d/',
        '/a/d/n',
        '/a/n',
        '/a/s/',
        '/a/s/w',
        '/a/s/e',
        '/k',
    )


del ProjectTestCase, TestNamingScheme

if __name__ == '__main__':
    main()

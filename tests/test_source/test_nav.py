import unittest
from abc import ABCMeta
from functools import cached_property
from textwrap import dedent

from typing_extensions import override

from abstracttests.projecttestcase import ProjectTestCase
from helpers import FakeFileSystem
from helpers.fakeproject import FakeProject, FakeVolume
from sobiraka.models import Page, Project, Status
from sobiraka.utils import RelativePath


class TestNav(ProjectTestCase, metaclass=ABCMeta):
    REQUIRE = Status.LOAD

    NAV_YAML: str
    TEXT_A = ''
    TEXT_B = ''
    TEXT_C = ''

    EXPECTED_ORDER = 'a', 'b', 'c'
    EXPECTED_TITLES: dict[str, str] = {'a': None, 'b': None, 'c': None}

    @override
    def _init_project(self) -> Project:
        return FakeProject({
            'src': FakeVolume({
                'chapter': {
                    '_nav.yaml': dedent(self.NAV_YAML).strip(),
                    'a': self.TEXT_A,
                    'b': self.TEXT_B,
                    'c': self.TEXT_C,
                }
            })
        })

    @cached_property
    def _chapter(self) -> Page:
        return self.project.get_volume().get_page_by_location('/chapter/')

    def _get_page(self, stem: str) -> Page:
        return self.project.get_volume().get_page_by_location(f'/chapter/{stem}')

    def test_order(self):
        actual = tuple(p.location.name for p in self._chapter.children)
        self.assertEqual(self.EXPECTED_ORDER, actual)

    def test_titles(self):
        for stem, expected in self.EXPECTED_TITLES.items():
            with self.subTest(**{stem: expected}):
                actual = self._get_page(stem).meta.title
                self.assertEqual(expected, actual)


class TestNav_Empty(TestNav):
    NAV_YAML = ''

    EXPECTED_ORDER = ()
    EXPECTED_TITLES = {}


class TestNav_Reorder(TestNav):
    NAV_YAML = '''
    items:
      - b
      - c
      - a
    '''

    EXPECTED_ORDER = 'b', 'c', 'a'


class TestNav_Rename(TestNav):
    NAV_YAML = '''
    items:
      - a: Page A renamed in Nav
      - b: Page B renamed in Nav but overridden in PageMeta
      - c
    '''
    TEXT_B = '---\ntitle: Page B renamed in PageMeta\n---'

    EXPECTED_TITLES = {'a': 'Page A renamed in Nav',
                       'b': 'Page B renamed in PageMeta',
                       'c': None}


class TestNav_SkipOne(TestNav):
    NAV_YAML = '''
    items:
      - a
      - c
    '''
    EXPECTED_ORDER = 'a', 'c'
    EXPECTED_TITLES = {'a': None, 'c': None}


class TestNav_Root(TestNav):
    NAV_YAML = '''
    items:
      - a
      - c
    '''
    EXPECTED_ORDER = 'a', 'c'
    EXPECTED_TITLES = {'a': None, 'c': None}

    @override
    def _init_project(self) -> Project:
        project = super()._init_project()
        fs: FakeFileSystem = project.fs
        fs.pseudofiles = {RelativePath(str(k).replace('/chapter', '')): v
                          for k, v in fs.pseudofiles.items()}
        return project

    @override
    @cached_property
    def _chapter(self) -> Page:
        return self.project.get_volume().root_page

    @override
    def _get_page(self, stem: str) -> Page:
        return self.project.get_volume().get_page_by_location(f'/{stem}')


del TestNav

if __name__ == '__main__':
    unittest.main()

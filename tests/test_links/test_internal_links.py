from unittest import main

from abstracttests.projecttestcase import ProjectTestCase
from helpers.fakeproject import FakeProject, FakeVolume
from sobiraka.models import PageHref, Project
from sobiraka.processing.latex import LatexBuilder
from sobiraka.processing.weasyprint import WeasyPrintBuilder
from sobiraka.processing.web import WebBuilder


class AbstractTestInternalLinks(ProjectTestCase):
    EXPECTED_THIS_PAGE: str
    EXPECTED_THIS_PAGE_SECTION: str
    EXPECTED_OTHER_PAGE: str
    EXPECTED_OTHER_PAGE_SECTION: str

    def _init_project(self) -> Project:
        return FakeProject({
            'src': FakeVolume({
                'this-page.md': '',
                'other-page.md': '',
            })
        })

    async def asyncSetUp(self):
        await super().asyncSetUp()
        volume = self.project.get_volume()
        self.this_page = volume.get_page_by_location('/this-page')
        self.other_page = volume.get_page_by_location('/other-page')

    def test_internal_links(self):
        with self.subTest('This page'):
            actual = self.builder.make_internal_url(PageHref(self.this_page), page=self.this_page)
            self.assertEqual(self.EXPECTED_THIS_PAGE, actual)

        with self.subTest('This page → Section'):
            actual = self.builder.make_internal_url(PageHref(self.this_page, 'section'), page=self.this_page)
            self.assertEqual(self.EXPECTED_THIS_PAGE_SECTION, actual)

        with self.subTest('Other page'):
            actual = self.builder.make_internal_url(PageHref(self.other_page), page=self.this_page)
            self.assertEqual(self.EXPECTED_OTHER_PAGE, actual)

        with self.subTest('Other page → Section'):
            actual = self.builder.make_internal_url(PageHref(self.other_page, 'section'), page=self.this_page)
            self.assertEqual(self.EXPECTED_OTHER_PAGE_SECTION, actual)


class TestInternalLinks_Latex(AbstractTestInternalLinks):
    def _init_builder(self):
        return LatexBuilder(self.project.get_volume(), None)

    EXPECTED_THIS_PAGE = '#r--this-page'
    EXPECTED_THIS_PAGE_SECTION = '#r--this-page--section'
    EXPECTED_OTHER_PAGE = '#r--other-page'
    EXPECTED_OTHER_PAGE_SECTION = '#r--other-page--section'


class TestInternalLinks_WeasyPrint(AbstractTestInternalLinks):
    def _init_builder(self):
        return WeasyPrintBuilder(self.project.get_volume(), None)

    EXPECTED_THIS_PAGE = '#this-page'
    EXPECTED_THIS_PAGE_SECTION = '#this-page::section'
    EXPECTED_OTHER_PAGE = '#other-page'
    EXPECTED_OTHER_PAGE_SECTION = '#other-page::section'


class TestInternalLinks_Web(AbstractTestInternalLinks):
    def _init_builder(self):
        return WebBuilder(self.project, None)

    EXPECTED_THIS_PAGE = ''
    EXPECTED_THIS_PAGE_SECTION = '#section'
    EXPECTED_OTHER_PAGE = 'other-page.html'
    EXPECTED_OTHER_PAGE_SECTION = 'other-page.html#section'


del AbstractTestInternalLinks

if __name__ == '__main__':
    main()

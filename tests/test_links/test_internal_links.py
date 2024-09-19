from unittest import main
from unittest.mock import Mock

from abstracttests.projecttestcase import ProjectTestCase
from sobiraka.models import FileSystem, Page, PageHref, Project, Volume
from sobiraka.processing import LatexBuilder, WeasyPrintBuilder, WebBuilder
from sobiraka.utils import RelativePath


class AbstractTestInternalLinks(ProjectTestCase):
    EXPECTED_THIS_PAGE: str
    EXPECTED_THIS_PAGE_SECTION: str
    EXPECTED_OTHER_PAGE: str
    EXPECTED_OTHER_PAGE_SECTION: str

    def _init_project(self) -> Project:
        fs = Mock(FileSystem)
        project = Project(fs, {
            RelativePath(): Volume({
                RelativePath('this-page.md'): Page(),
                RelativePath('other-page.md'): Page(),
            })
        })
        self.this_page = project.pages_by_path[RelativePath('this-page.md')]
        self.other_page = project.pages_by_path[RelativePath('other-page.md')]
        return project

    def test_internal_links(self):
        with self.subTest('This page'):
            actual = self.processor.make_internal_url(PageHref(self.this_page), page=self.this_page)
            self.assertEqual(self.EXPECTED_THIS_PAGE, actual)

        with self.subTest('This page → Section'):
            actual = self.processor.make_internal_url(PageHref(self.this_page, 'section'), page=self.this_page)
            self.assertEqual(self.EXPECTED_THIS_PAGE_SECTION, actual)

        with self.subTest('Other page'):
            actual = self.processor.make_internal_url(PageHref(self.other_page), page=self.this_page)
            self.assertEqual(self.EXPECTED_OTHER_PAGE, actual)

        with self.subTest('Other page → Section'):
            actual = self.processor.make_internal_url(PageHref(self.other_page, 'section'), page=self.this_page)
            self.assertEqual(self.EXPECTED_OTHER_PAGE_SECTION, actual)


class TestInternalLinks_HTML(AbstractTestInternalLinks):
    def _init_processor(self):
        return WebBuilder(self.project, None)

    EXPECTED_THIS_PAGE = ''
    EXPECTED_THIS_PAGE_SECTION = '#section'
    EXPECTED_OTHER_PAGE = 'other-page.html'
    EXPECTED_OTHER_PAGE_SECTION = 'other-page.html#section'


class TestInternalLinks_Latex(AbstractTestInternalLinks):
    def _init_processor(self):
        return LatexBuilder(self.project.get_volume(), None)

    EXPECTED_THIS_PAGE = '#r--this-page'
    EXPECTED_THIS_PAGE_SECTION = '#r--this-page--section'
    EXPECTED_OTHER_PAGE = '#r--other-page'
    EXPECTED_OTHER_PAGE_SECTION = '#r--other-page--section'


class TestInternalLinks_WeasyPrint(AbstractTestInternalLinks):
    def _init_processor(self):
        return WeasyPrintBuilder(self.project.get_volume(), None)

    EXPECTED_THIS_PAGE = '#this-page.md'
    EXPECTED_THIS_PAGE_SECTION = '#this-page.md::section'
    EXPECTED_OTHER_PAGE = '#other-page.md'
    EXPECTED_OTHER_PAGE_SECTION = '#other-page.md::section'


del AbstractTestInternalLinks

if __name__ == '__main__':
    main()
